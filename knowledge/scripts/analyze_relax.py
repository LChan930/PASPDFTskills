#!/usr/bin/env python3
"""Analyze native PASP fixed-cell ionic relaxation logs offline (Python 3.10+)."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path

from audit_inputs import FALSE, TRUE, Audit, integer, number

BOHR_TO_ANGSTROM = 0.529177210903
HA_PER_BOHR_TO_EV_PER_ANGSTROM = 51.42208  # Conversion used by the ionic force test.
FORCE_COMPONENT_RESOLUTION = 1e-6
FORCE_NORM_ROUNDING = math.sqrt(3) * FORCE_COMPONENT_RESOLUTION / 2
STEP = re.compile(r"^-+\s*iteration for ionic relaxation:\s*(.*?)$", re.IGNORECASE)
TABLE_START = re.compile(r"^=+\s*POSITION and FORCE\s*=+$", re.IGNORECASE)
TABLE_END = re.compile(r"^=+\s*POSITION and FORCE END\s*=+$", re.IGNORECASE)
TABLE_HEADER = re.compile(r"^atom\s+POSITION\s+FORCE$", re.IGNORECASE)
ENERGY = re.compile(r"^Total energy \(in Hartree\) is:\s*(.*?)$", re.IGNORECASE)
SCF = re.compile(r"^PASP_SCF_RESULT\s+.*?\bstatus=(\w+)(?:\s|$)", re.IGNORECASE)
CERTIFIED = re.compile(r"\bcertified=([TF])(?:\s|$)", re.IGNORECASE)
SCF_WARNING = re.compile(
    r"^(?:WARNING:\s*SCF iteration budget exhausted\b|"
    r"(?:PW(?:_RELAX|_DFT|_MD)?\s*:\s*)?self-consistent iteration failed\b)",
    re.IGNORECASE,
)
FATAL = re.compile(
    r"^(?:ERROR STOP\b|MPI_ABORT was invoked\b|forrtl:\s*severe\b)", re.IGNORECASE
)
SCF_FAILURES = {
    "FAILED",
    "FAILURE",
    "MAXITER",
    "NUMERICAL_FAILURE",
    "UNCONVERGED",
    "NONCONVERGED",
    "NOT_CONVERGED",
}
IONIC_MARKERS = (
    (
        "converged",
        re.compile(
            r"^reached required accuracy\s*-\s*stopping structural energy minimisation\.",
            re.IGNORECASE,
        ),
    ),
    ("nstep_limit", re.compile(r"^Warning:\s*NSTEP Reached\b", re.IGNORECASE)),
    (
        "optimizer_failed",
        re.compile(
            r"^Warning:\s*DFT relax fail \(CG stopped ungracefully\)", re.IGNORECASE
        ),
    ),
)
ELEMENTS = frozenset(
    [
        "H",
        "He",
        "Li",
        "Be",
        "B",
        "C",
        "N",
        "O",
        "F",
        "Ne",
        "Na",
        "Mg",
        "Al",
        "Si",
        "P",
        "S",
        "Cl",
        "Ar",
        "K",
        "Ca",
        "Sc",
        "Ti",
        "V",
        "Cr",
        "Mn",
        "Fe",
        "Co",
        "Ni",
        "Cu",
        "Zn",
        "Ga",
        "Ge",
        "As",
        "Se",
        "Br",
        "Kr",
        "Rb",
        "Sr",
        "Y",
        "Zr",
        "Nb",
        "Mo",
        "Tc",
        "Ru",
        "Rh",
        "Pd",
        "Ag",
        "Cd",
        "In",
        "Sn",
        "Sb",
        "Te",
        "I",
        "Xe",
        "Cs",
        "Ba",
        "La",
        "Ce",
        "Pr",
        "Nd",
        "Pm",
        "Sm",
        "Eu",
        "Gd",
        "Tb",
        "Dy",
        "Ho",
        "Er",
        "Tm",
        "Yb",
        "Lu",
        "Hf",
        "Ta",
        "W",
        "Re",
        "Os",
        "Ir",
        "Pt",
        "Au",
        "Hg",
        "Tl",
        "Pb",
        "Bi",
        "Po",
        "At",
        "Rn",
        "Fr",
        "Ra",
        "Ac",
        "Th",
        "Pa",
        "U",
        "Np",
        "Pu",
        "Am",
        "Cm",
        "Bk",
        "Cf",
        "Es",
        "Fm",
        "Md",
        "No",
        "Lr",
        "Rf",
        "Db",
        "Sg",
        "Bh",
        "Hs",
        "Mt",
        "Ds",
        "Rg",
        "Cn",
        "Nh",
        "Fl",
        "Mc",
        "Lv",
        "Ts",
        "Og",
    ]
)


def finding(code: str, *evidence: dict, severity: str = "error") -> dict:
    return {"code": code, "severity": severity, "evidence": list(evidence)}


@dataclass
class ForceTable:
    step: int
    start: dict
    step_header: dict | None
    header_seen: bool = False
    atoms: list[dict] = field(default_factory=list)
    invalid: bool = False

    def row(self, raw: str, evidence: dict) -> None:
        line = evidence["text"]
        if TABLE_HEADER.fullmatch(line) and not self.header_seen and not self.atoms:
            self.header_seen = True
            return
        tokens = line.split()
        if len(tokens) != 7 and len(raw) == 69 and raw[37:39] == "  ":
            # Native I7,3F10.6,2X,3F10.6 fields can touch at their width limits.
            tokens = [raw[:7], *(raw[i : i + 10] for i in (7, 17, 27, 39, 49, 59))]
        if not self.header_seen or len(tokens) != 7:
            raise ValueError("invalid table row")
        atom_id = integer(tokens[0].strip())
        if atom_id != len(self.atoms) + 1:
            raise ValueError("noncontiguous atom ID")
        coordinates = [number(token) for token in tokens[1:]]
        force_norm = math.hypot(*coordinates[3:])
        if not math.isfinite(force_norm * HA_PER_BOHR_TO_EV_PER_ANGSTROM):
            raise ValueError("nonfinite force norm")
        self.atoms.append(
            {
                "atom_id": atom_id,
                "position_bohr": coordinates[:3],
                "force_ha_per_bohr": coordinates[3:],
                "force_norm_ha_per_bohr": force_norm,
                "line": evidence["line"],
            }
        )


class RelaxationLog:
    def __init__(self) -> None:
        self.start = None
        self.fixed_cell = None
        self.graceful = None
        self.ionic_markers = []
        self.fatals = []
        self.electronic = []
        self.pending_scf = []
        self.pending_energies = []
        self.step_header = None
        self.table = None
        self.table_count = 0
        self.frames = []
        self.last_geometry = None
        self.atom_count = None
        self.findings = []
        self.ambiguous = False
        self.ionic_layout_seen = False

    def finish_table(self, end: dict) -> None:
        table = self.table
        self.table = None
        if table.invalid:
            self.pending_scf.clear()
            self.pending_energies.clear()
            return
        if not table.atoms or self.atom_count not in (None, len(table.atoms)):
            self.findings.append(finding("inconsistent_atom_count", table.start, end))
            self.pending_scf.clear()
            self.pending_energies.clear()
            return
        self.atom_count = len(table.atoms)
        energy, energy_evidence = None, None
        if len(self.pending_energies) == 1:
            energy, energy_evidence = self.pending_energies[0]
        else:
            code = "missing_energy" if not self.pending_energies else "ambiguous_energy"
            self.findings.append(
                finding(
                    code,
                    *(evidence for _, evidence in self.pending_energies),
                    table.start,
                )
            )
        self.pending_energies.clear()
        previous = self.frames[-1] if self.frames else None
        delta = None
        if (
            energy is not None
            and previous
            and previous["step"] == table.step - 1
            and (previous_energy := previous["energy_ha"]) is not None
        ):
            delta = energy - previous_energy
            if not math.isfinite(delta):
                self.findings.append(
                    finding("nonfinite_energy_difference", energy_evidence)
                )
                delta = None
        maximum = max(table.atoms, key=lambda atom: atom["force_norm_ha_per_bohr"])
        norm = maximum["force_norm_ha_per_bohr"]
        evidence = {
            "step_header": table.step_header,
            "energy": energy_evidence,
            "table_start": table.start,
            "table_end": end,
        }
        self.frames.append(
            {
                "step": table.step,
                "energy_ha": energy,
                "delta_energy_ha": delta,
                "max_force_ha_per_bohr": norm,
                "max_force_ev_per_angstrom": norm * HA_PER_BOHR_TO_EV_PER_ANGSTROM,
                "max_force_atom_id": maximum["atom_id"],
                "max_force_atom_line": maximum["line"],
                "electronic_evidence": self.pending_scf.copy(),
                "evidence": evidence,
            }
        )
        self.pending_scf.clear()
        self.last_geometry = {
            "step": table.step,
            "atoms": table.atoms,
            "source": "rounded_cartesian_log_table",
            "coordinate_units": "Bohr",
            "label_source": "atom_id",
            "evidence": evidence,
        }

    def conflict(self, code: str, *evidence: dict) -> None:
        self.findings.append(finding(code, *evidence))
        self.ambiguous = True

    def scan(self, raw: str, line_number: int) -> None:
        line = raw.strip()
        if not line:
            return
        evidence = {"line": line_number, "text": line}
        folded = line.casefold()
        if folded == "pasp start":
            if (
                self.start
                or self.fixed_cell
                or self.table_count
                or self.ionic_markers
                or self.graceful
            ):
                self.conflict("repeated_run", evidence)
            else:
                self.start = evidence
            return
        if folded.startswith("pasp_relax_fixed_cell"):
            self.ionic_layout_seen = True
            if self.fixed_cell or self.table_count or self.graceful:
                self.conflict("repeated_run", evidence)
            elif not re.search(
                r"\benabled=T\s+cell_dof=disabled\b", line, re.IGNORECASE
            ):
                self.conflict("unsupported_relaxation_marker", evidence)
            else:
                self.fixed_cell = evidence
            return
        if match := STEP.fullmatch(line):
            self.ionic_layout_seen = True
            if (
                self.table
                or self.step_header
                or self.ionic_markers
                or self.graceful
                or not self.table_count
                or not re.fullmatch(r"[0-9]{1,9}", match[1])
                or int(match[1]) != self.table_count
            ):
                self.conflict("unexpected_step_header", evidence)
            else:
                self.step_header = evidence
            return
        if TABLE_START.fullmatch(line):
            if (
                self.table
                or self.ionic_markers
                or self.graceful
                or (self.table_count and not self.step_header)
            ):
                self.conflict("unexpected_force_table", evidence)
            elif not self.ambiguous:
                self.table = ForceTable(self.table_count, evidence, self.step_header)
                self.table_count += 1
                self.step_header = None
            return
        if TABLE_END.fullmatch(line):
            if self.table and not self.ambiguous:
                self.finish_table(evidence)
            elif not self.ambiguous:
                self.conflict("unexpected_table_end", evidence)
            return
        if folded == "pasp is finished gracefully.":
            if self.graceful:
                self.conflict("repeated_run", self.graceful, evidence)
            else:
                self.graceful = evidence
            return
        for status, marker in IONIC_MARKERS:
            if marker.match(line):
                self.ionic_layout_seen = True
                if (
                    self.table
                    or self.step_header
                    or self.pending_energies
                    or self.pending_scf
                    or self.graceful
                ):
                    self.conflict("misplaced_ionic_exit", evidence)
                if self.ionic_markers:
                    self.conflict(
                        "repeated_ionic_exit", self.ionic_markers[0][1], evidence
                    )
                self.ionic_markers.append((status, evidence))
                return
        if FATAL.match(line):
            self.fatals.append(evidence)
            return
        if self.ambiguous:
            return
        if self.table:
            if not self.table.invalid:
                try:
                    self.table.row(raw, evidence)
                except ValueError:
                    self.table.invalid = True
                    self.findings.append(
                        finding("invalid_force_table_row", self.table.start, evidence)
                    )
            return
        if match := SCF.match(line):
            result = {**evidence, "status": match[1].upper()}
            certified = CERTIFIED.search(line)
            result["certified"] = certified[1].upper() == "T" if certified else None
            self.electronic.append(result)
            self.pending_scf.append(result)
        elif SCF_WARNING.match(line) or folded.startswith("pasp_scf_result"):
            status = (
                "failure_message" if SCF_WARNING.match(line) else "unrecognized_result"
            )
            result = {**evidence, "status": status, "certified": None}
            self.electronic.append(result)
            self.pending_scf.append(result)
        elif match := ENERGY.fullmatch(line):
            try:
                energy = number(match[1])
            except ValueError:
                self.findings.append(finding("invalid_energy", evidence))
                energy = None
            self.pending_energies.append((energy, evidence))

    def summarize(self) -> tuple[dict, dict, dict]:
        if not self.ionic_layout_seen:
            self.findings.append(finding("no_relaxation_evidence"))
            self.frames.clear()
            self.last_geometry = None
        if not self.frames:
            self.findings.append(finding("no_complete_geometry"))
        if self.table or self.step_header:
            self.findings.append(
                finding(
                    "truncated_force_table",
                    self.table.start if self.table else self.step_header,
                )
            )
        if self.pending_energies or self.pending_scf:
            self.findings.append(
                finding(
                    "unpaired_electronic_stage",
                    *(e for _, e in self.pending_energies),
                    *self.pending_scf,
                )
            )
        ionic = {
            "status": "not_reported",
            "evidence": [e for _, e in self.ionic_markers],
        }
        if self.ambiguous:
            ionic["status"] = "ambiguous"
        elif self.ionic_markers:
            ionic["status"] = self.ionic_markers[0][0]
        if not self.ionic_markers:
            self.findings.append(finding("missing_ionic_exit"))
        if self.fatals:
            self.findings.append(finding("process_failure", *self.fatals))
        if not self.graceful:
            self.findings.append(finding("missing_graceful_finish"))
        completion_status = "incomplete"
        if self.fatals:
            completion_status = "failed"
        elif self.graceful:
            completion_status = "graceful"
        if any(item["code"] == "repeated_run" for item in self.findings):
            completion_status = "ambiguous"
        completion = {
            "status": completion_status,
            "evidence": ([self.graceful] if self.graceful else []) + self.fatals,
        }
        failures = [
            r
            for r in self.electronic
            if r["status"] in SCF_FAILURES | {"failure_message"}
        ]
        if failures:
            electronic_status = "failure_evidence_present"
            self.findings.append(finding("scf_failure", *failures))
        elif any(r["status"] == "unrecognized_result" for r in self.electronic):
            electronic_status = "ambiguous"
            self.findings.append(finding("unrecognized_scf_result", *self.electronic))
        elif self.electronic:
            electronic_status = "explicit_result_records_present"
        else:
            electronic_status = "no_explicit_protocol"
        electronic = {"status": electronic_status, "evidence": self.electronic}
        return ionic, completion, electronic


def read_log(path: Path) -> tuple[dict, RelaxationLog]:
    result = RelaxationLog()
    sha256 = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for line, raw in enumerate(stream, 1):
            sha256.update(raw)
            size += len(raw)
            encoding = "utf-8-sig" if line == 1 else "utf-8"
            result.scan(raw.decode(encoding).rstrip("\r\n"), line)
    return {
        "path": str(path.resolve()),
        "bytes": size,
        "sha256": sha256.hexdigest(),
        "fixed_cell_marker": result.fixed_cell,
    }, result


def logical(value: str) -> bool:
    value = value.lower()
    if value not in TRUE | FALSE:
        raise ValueError("expected a logical scalar")
    return value in TRUE


def read_requested_input(path: Path, findings: list[dict]) -> dict:
    if not path.is_file():
        raise OSError(f"input file is not a readable file: {path}")
    with path.open("rb"):
        pass
    audit = Audit(path, None, None)
    audit.expand(path)
    audit.parse()
    for item in audit.findings:
        if item["severity"] == "ERROR" or item["code"] in {
            "ambiguous_include_base",
            "include_parent_fallback",
        }:
            findings.append(
                finding(
                    "input_audit_issue",
                    *item["anchors"],
                    severity=item["severity"].lower(),
                )
                | {"detail": item}
            )
    settings = {}
    for tag, parse in {
        "dft.ediffg": number,
        "dft.nstep": integer,
        "numberofatoms": integer,
        "dft.lrelax": logical,
        "dft.relax.fixed_cell": logical,
    }.items():
        rows = audit.scalars[tag]
        if len(rows) > 1:
            findings.append(
                finding("duplicate_input_setting", *(row["anchor"] for row in rows))
                | {"tag": tag}
            )
        elif rows:
            row = rows[0]
            try:
                (value,) = row["tokens"]
                settings[tag] = {"value": parse(value), "evidence": row["anchor"]}
            except ValueError:
                findings.append(
                    finding("invalid_input_setting", row["anchor"]) | {"tag": tag}
                )
    return {
        "path": str(path.resolve()),
        "settings": settings,
        "files": list(audit.files.values()),
        "includes": audit.includes,
        "interpretation": "requested_settings_only",
    }


def compare_input(requested: dict | None, log: RelaxationLog, ionic: dict) -> dict:
    settings = requested["settings"] if requested else {}
    last = log.frames[-1] if log.frames else None
    for tag in ("dft.lrelax", "dft.relax.fixed_cell"):
        if tag in settings and not settings[tag]["value"]:
            log.findings.append(
                finding("input_workflow_mismatch", settings[tag]["evidence"])
                | {"tag": tag}
            )
    if (
        last
        and (nat := settings.get("numberofatoms"))
        and nat["value"] != log.atom_count
    ):
        log.findings.append(
            finding(
                "input_atom_count_mismatch",
                nat["evidence"],
                last["evidence"]["table_end"],
            )
        )
    if (
        last
        and (nstep := settings.get("dft.nstep"))
        and (
            last["step"] > nstep["value"]
            or (ionic["status"] == "nstep_limit" and last["step"] != nstep["value"])
        )
    ):
        log.findings.append(
            finding(
                "input_nstep_mismatch", nstep["evidence"], last["evidence"]["table_end"]
            )
        )

    ediffg = settings.get("dft.ediffg")
    if ediffg is None:
        return {"status": "not_reported", "setting": None}
    value = ediffg["value"]
    threshold = {
        "status": "zero_setting",
        "setting": ediffg,
        "step": last["step"] if last else None,
    }
    if value > 0:
        delta = last["delta_energy_ha"] if last else None
        threshold.update(
            status="optimizer_specific",
            criterion="ionic_optimizer_energy",
            threshold_ha=value,
            absolute_delta_energy_ha=abs(delta) if delta is not None else None,
        )
    if value < 0:
        tolerance = FORCE_NORM_ROUNDING * HA_PER_BOHR_TO_EV_PER_ANGSTROM
        threshold.update(
            status="no_complete_frame",
            criterion="max_force_norm",
            threshold_ev_per_angstrom=abs(value),
            rounding_uncertainty_ev_per_angstrom=tolerance,
        )
        if last:
            force = last["max_force_ev_per_angstrom"]
            low, high = max(0.0, force - tolerance), force + tolerance
            status = "within_rounding_uncertainty"
            if high <= abs(value):
                status = "below_threshold"
            elif low > abs(value):
                status = "above_threshold"
            threshold.update(
                status=status,
                printed_max_force_ev_per_angstrom=force,
                possible_max_force_ev_per_angstrom=[low, high],
            )
            if status == "above_threshold" and ionic["status"] == "converged":
                log.findings.append(
                    finding(
                        "requested_threshold_disagrees_with_exit",
                        ediffg["evidence"],
                        last["evidence"]["table_end"],
                        *ionic["evidence"],
                        severity="warning",
                    )
                )
    return threshold


def analyze(log_path: Path, input_path: Path | None) -> dict:
    source, log = read_log(log_path)
    ionic, completion, electronic = log.summarize()
    requested = read_requested_input(input_path, log.findings) if input_path else None
    threshold = compare_input(requested, log, ionic)
    return {
        "schema_version": 1,
        "log": source,
        "input": requested,
        "ionic_exit": ionic,
        "run_completion": completion,
        "electronic_status": electronic,
        "threshold": threshold,
        "frames": log.frames,
        "last_complete_geometry": log.last_geometry,
        "units": {
            "energy": "Ha",
            "positions": "Bohr",
            "printed_force": "Ha/Bohr",
            "converted_force": "eV/Å",
            "printed_force_component_resolution_ha_per_bohr": FORCE_COMPONENT_RESOLUTION,
            "ha_per_bohr_to_ev_per_angstrom": HA_PER_BOHR_TO_EV_PER_ANGSTROM,
            "bohr_to_angstrom": BOHR_TO_ANGSTROM,
        },
        "findings": log.findings,
    }


LANGUAGES = ("en", "zh-Hans", "zh-Hant")
TEXT = {
    "title": (
        "PASP fixed-cell ionic relaxation",
        "PASP 固定晶胞离子弛豫",
        "PASP 固定晶胞離子弛豫",
    ),
    "log": ("Log", "日志", "日誌"),
    "input": ("Requested input", "输入文件中的请求设置", "輸入檔案中的請求設定"),
    "ionic_exit": ("Ionic exit", "离子优化退出", "離子最佳化退出"),
    "run_completion": ("Run completion", "运行结束状态", "執行結束狀態"),
    "electronic_status": ("Electronic evidence", "电子迭代证据", "電子迭代證據"),
    "threshold": ("Threshold evidence", "阈值证据", "閾值證據"),
    "line": ("line", "行", "行"),
    "frames": ("Complete ionic frames", "完整离子步", "完整離子步"),
    "step": ("Step", "步", "步"),
    "energy": ("Energy", "能量", "能量"),
    "force": ("Max force norm", "最大力范数", "最大力範數"),
    "atom": ("Atom ID", "原子编号", "原子編號"),
    "table_lines": ("Table lines", "表格行号", "表格行號"),
    "geometry": (
        "Last complete Cartesian geometry",
        "最后一帧完整笛卡尔坐标",
        "最後一幀完整笛卡兒座標",
    ),
    "none": ("None", "无", "無"),
    "findings": ("Findings", "检查结果", "檢查結果"),
    "rounded": (
        "Coordinates come from the rounded log table. Use a native restart artifact to restart PASP.",
        "坐标来自日志中的舍入表格。重新启动 PASP 应使用原生重启文件。",
        "座標來自日誌中的捨入表格。重新啟動 PASP 應使用原生重啟檔案。",
    ),
    "input_note": (
        "FDF values describe the supplied file. The log determines the reported ionic exit.",
        "FDF 数值反映提供的输入文件。离子优化退出状态以日志为准。",
        "FDF 數值反映提供的輸入檔案。離子最佳化退出狀態以日誌為準。",
    ),
    "force_note": (
        "The range accounts for six-decimal rounding of the printed force components.",
        "区间包含日志中力分量保留六位小数产生的舍入误差。",
        "區間包含日誌中力分量保留六位小數產生的捨入誤差。",
    ),
    "energy_note": (
        "Adjacent printed energy differences are diagnostic. The optimizer also uses its internal state and trial energy.",
        "相邻打印能量的差值用于诊断。优化器还使用内部状态和试探能量。",
        "相鄰列印能量的差值用於診斷。最佳化器還使用內部狀態和試探能量。",
    ),
    "converged": ("Convergence marker present", "日志报告离子收敛", "日誌報告離子收斂"),
    "nstep_limit": ("NSTEP limit reached", "达到 NSTEP 上限", "達到 NSTEP 上限"),
    "optimizer_failed": ("Optimizer failure", "优化器失败", "最佳化器失敗"),
    "not_reported": ("Unreported", "未报告", "未報告"),
    "ambiguous": ("Ambiguous evidence", "证据存在歧义", "證據存在歧義"),
    "graceful": (
        "Graceful finish marker present",
        "日志报告正常结束",
        "日誌報告正常結束",
    ),
    "incomplete": ("Completion unconfirmed", "结束状态未确认", "結束狀態未確認"),
    "failed": (
        "Process failure marker present",
        "日志报告进程失败",
        "日誌報告程序失敗",
    ),
    "failure_evidence_present": (
        "SCF failure evidence present",
        "存在 SCF 失败证据",
        "存在 SCF 失敗證據",
    ),
    "explicit_result_records_present": (
        "Explicit SCF result records present",
        "存在显式 SCF 结果",
        "存在明確的 SCF 結果",
    ),
    "no_explicit_protocol": (
        "No explicit SCF result records",
        "无显式 SCF 结果",
        "無明確的 SCF 結果",
    ),
    "zero_setting": ("EDIFFG is zero", "EDIFFG 为零", "EDIFFG 為零"),
    "optimizer_specific": (
        "Optimizer-specific energy test",
        "优化器专用能量判据",
        "最佳化器專用能量判據",
    ),
    "no_complete_frame": ("No complete frame", "无完整帧", "無完整幀"),
    "below_threshold": (
        "Within force threshold",
        "处于力阈值范围内",
        "處於力閾值範圍內",
    ),
    "above_threshold": ("Above force threshold", "高于力阈值", "高於力閾值"),
    "within_rounding_uncertainty": (
        "Force range overlaps threshold",
        "力的区间与阈值重叠",
        "力的區間與閾值重疊",
    ),
}


def display_number(value: float | None, form: str = ".9g") -> str:
    return "—" if value is None else format(value, form)


def render_markdown(report: dict, lang: str) -> str:
    language = LANGUAGES.index(lang)
    captions = {key: options[language] for key, options in TEXT.items()}
    log = report["log"]
    output = [
        f"# {captions['title']}",
        "",
        f"- {captions['log']} `{log['path']}` (SHA-256 `{log['sha256']}`)",
    ]
    if requested := report["input"]:
        output.extend(
            [
                f"- {captions['input']} `{requested['path']}`",
                f"- {captions['input_note']}",
            ]
        )
    for key in ("ionic_exit", "run_completion", "electronic_status", "threshold"):
        status = report[key]
        evidence = status.get("evidence", [])
        label = f"- {captions[key]} · {captions[status['status']]}"
        if evidence:
            last = evidence[-1]
            label += f" ({captions['line']} {last['line']}) `{last['text']}`"
            if len(evidence) > 1:
                label += f" ({len(evidence)} records)"
        output.append(label)
    threshold = report["threshold"]
    if setting := threshold["setting"]:
        output.append(
            f"  - `DFT.EDIFFG {setting['value']:.9g}` (`{setting['evidence']['file']}`, {captions['line']} {setting['evidence']['line']})"
        )
    if "possible_max_force_ev_per_angstrom" in threshold:
        low, high = threshold["possible_max_force_ev_per_angstrom"]
        output.append(f"  - [{low:.8g}, {high:.8g}] eV/Å · {captions['force_note']}")
    if threshold["status"] == "optimizer_specific":
        output.append(
            f"  - |ΔE| = {display_number(threshold['absolute_delta_energy_ha'])} Ha · {captions['energy_note']}"
        )

    output.extend(["", f"## {captions['frames']}", ""])
    if report["frames"]:
        output.extend(
            [
                f"| {captions['step']} | {captions['energy']} (Ha) | ΔE (Ha) | {captions['force']} (Ha/Bohr) | {captions['force']} (eV/Å) | {captions['atom']} | SCF | {captions['table_lines']} |",
                "| ---: | ---: | ---: | ---: | ---: | ---: | :--- | ---: |",
            ]
        )
        for frame in report["frames"]:
            ev = frame["evidence"]
            scf = ", ".join(
                dict.fromkeys(record["status"] for record in frame["electronic_evidence"])
            ) or "—"
            output.append(
                f"| {frame['step']} | {display_number(frame['energy_ha'], '.12f')} | "
                f"{display_number(frame['delta_energy_ha'])} | {frame['max_force_ha_per_bohr']:.8g} | "
                f"{frame['max_force_ev_per_angstrom']:.8g} | {frame['max_force_atom_id']} | "
                f"{scf} | {ev['table_start']['line']}–{ev['table_end']['line']} |"
            )
    else:
        output.append(captions["none"])
    if geometry := report["last_complete_geometry"]:
        output.extend(
            [
                "",
                f"## {captions['geometry']} ({captions['step']} {geometry['step']})",
                "",
                captions["rounded"],
                "",
                f"| {captions['atom']} | x (Bohr) | y (Bohr) | z (Bohr) | {captions['line']} |",
                "| ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for atom in geometry["atoms"]:
            x, y, z = atom["position_bohr"]
            output.append(
                f"| {atom['atom_id']} | {x:.6f} | {y:.6f} | {z:.6f} | {atom['line']} |"
            )
    if report["findings"]:
        output.extend(["", f"## {captions['findings']}", ""])
        for item in report["findings"]:
            anchors = ", ".join(
                f"{captions['line']} {e['line']}" for e in item["evidence"]
            )
            detail = f" ({anchors})" if anchors else ""
            output.append(f"- `{item['code']}`{detail}")
    return "\n".join(output) + "\n"


def render_xyz(report: dict, symbols: list[str]) -> bytes:
    geometry = report["last_complete_geometry"]
    atoms = geometry["atoms"]
    if len(atoms) != len(symbols):
        raise ValueError(
            f"--symbols requires one actual element per atom, in atom-ID order ({len(atoms)} needed)"
        )
    evidence = geometry["evidence"]
    source = json.dumps(report["log"]["path"], ensure_ascii=False)
    comment = (
        f"Rounded PASP Cartesian coordinates in Angstrom, step {geometry['step']}, "
        f"log lines {evidence['table_start']['line']}-{evidence['table_end']['line']}, source {source}, "
        "element symbols supplied in atom-ID order. Use a native artifact to restart PASP."
    )
    rows = [str(len(atoms)), comment]
    for symbol, atom in zip(symbols, atoms):
        x, y, z = (value * BOHR_TO_ANGSTROM for value in atom["position_bohr"])
        rows.append(f"{symbol} {x:.7f} {y:.7f} {z:.7f}")
    return ("\n".join(rows) + "\n").encode("utf-8")


def render_plot(frames: list[dict]) -> bytes:
    try:
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.figure import Figure
    except ImportError as exc:
        raise ValueError("--plot requires Matplotlib") from exc

    figure = Figure(figsize=(7.0, 5.0), layout="constrained")
    FigureCanvasAgg(figure)
    energy_axis, force_axis = figure.subplots(2, 1, sharex=True)
    steps = [frame["step"] for frame in frames]
    energy = [
        math.nan if frame["energy_ha"] is None else frame["energy_ha"]
        for frame in frames
    ]
    force = [frame["max_force_ev_per_angstrom"] for frame in frames]
    energy_axis.plot(steps, energy, "o-", color="#1a5276", markersize=3)
    force_axis.plot(steps, force, "o-", color="#9c3f20", markersize=3)
    energy_axis.set_ylabel("Total energy (Ha)")
    force_axis.set_ylabel("Max force norm (eV/Å)")
    force_axis.set_xlabel("Ionic step")
    for axis in (energy_axis, force_axis):
        axis.grid(alpha=0.25)
    output = BytesIO()
    figure.savefig(output, format="png", dpi=160)
    return output.getvalue()


def check_destinations(args: argparse.Namespace) -> None:
    destinations = set()
    for path, suffix in ((args.output, None), (args.plot, ".png"), (args.xyz, ".xyz")):
        if path is None:
            continue
        if suffix and path.suffix.lower() != suffix:
            raise ValueError(f"output filename must end in {suffix}: {path}")
        if path.exists() or path.is_symlink():
            raise FileExistsError(f"output already exists: {path}")
        if not path.parent.is_dir():
            raise ValueError(f"output parent directory does not exist: {path.parent}")
        resolved = path.resolve()
        if resolved in destinations:
            raise ValueError(f"outputs must use different paths: {path}")
        destinations.add(resolved)


def write_outputs(outputs: list[tuple[Path, bytes]]) -> None:
    created = []
    try:
        for path, data in outputs:
            with path.open("xb") as stream:
                created.append((path, os.fstat(stream.fileno())))
                stream.write(data)
    except OSError:
        for path, identity in created:
            try:
                if os.path.samestat(path.lstat(), identity):
                    path.unlink()
            except OSError:
                pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "log", type=Path, metavar="LOG", help="Native relaxation log of any filename"
    )
    parser.add_argument(
        "--input",
        type=Path,
        metavar="FDF",
        help="Optional matching input for requested settings",
    )
    parser.add_argument(
        "--lang",
        choices=LANGUAGES,
        default="en",
        help="Markdown language (default: en)",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Report format (default: markdown)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        metavar="NEW_FILE",
        help="Create a report file instead of writing to stdout",
    )
    parser.add_argument(
        "--plot",
        type=Path,
        metavar="NEW.png",
        help="Create a convergence plot (requires Matplotlib)",
    )
    parser.add_argument(
        "--xyz",
        type=Path,
        metavar="NEW.xyz",
        help="Export rounded last-frame Cartesian coordinates in Å",
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        metavar="ELEMENT",
        help="Actual element symbols in atom-ID order for --xyz",
    )
    args = parser.parse_args()
    if bool(args.xyz) != bool(args.symbols):
        parser.error("--xyz and --symbols are required together")
    if args.symbols and (
        bad := [symbol for symbol in args.symbols if symbol not in ELEMENTS]
    ):
        parser.error("unknown element symbol(s): " + ", ".join(bad))
    try:
        check_destinations(args)
        report = analyze(args.log, args.input)
        rendered = (
            json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
            if args.format == "json"
            else render_markdown(report, args.lang)
        )
        report_bytes = rendered.encode("utf-8")
        outputs = []
        if args.output:
            outputs.append((args.output, report_bytes))
        if report["last_complete_geometry"]:
            if args.xyz:
                outputs.append((args.xyz, render_xyz(report, args.symbols)))
            if args.plot:
                outputs.append((args.plot, render_plot(report["frames"])))
        write_outputs(outputs)
        if not args.output:
            sys.stdout.buffer.write(report_bytes)
    except (OSError, ValueError) as exc:
        print(f"analyze_relax: {exc}", file=sys.stderr)
        return 2
    complete = (
        report["ionic_exit"]["status"] in {"converged", "nstep_limit"}
        and report["run_completion"]["status"] == "graceful"
        and not any(item["severity"] == "error" for item in report["findings"])
    )
    return 0 if complete else 1


if __name__ == "__main__":
    sys.exit(main())
