#!/usr/bin/env python3
"""Read native PASP MD text without PASP, private scripts, or production source.

Python 3.10+, standard library; optional plotting uses Matplotlib. Atom arrays
are validated one frame at a time; only scalar observables are retained.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
import sys
from pathlib import Path

NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][-+]?\d+)?|[-+]?(?:nan|inf(?:inity)?)"
STEP = re.compile(r"^Step\s*=\s*(\d+)(?:\s*;\s*(.*))?$", re.IGNORECASE)
SCALAR = re.compile(
    r"(Time|E_p|E_k|E_?tot|Temp|H)\s*\(([^)]+)\)\s*=\s*(" + NUMBER + r")", re.IGNORECASE
)
SECTION = re.compile(r"^(xa|va|fa|lattice|stress):\s*\(([^)]+)\)\s*$", re.IGNORECASE)
LOG_ROW = re.compile(
    r"^\s*(\d+)\s+("
    + NUMBER
    + r")\s+(\d+)\s+("
    + NUMBER
    + r")\s+("
    + NUMBER
    + r")\s*$",
    re.IGNORECASE,
)
NAMES = {
    "time": "time_fs",
    "e_p": "Ep_Ha",
    "e_k": "Ek_Ha",
    "etot": "Etot_Ha",
    "e_tot": "Etot_Ha",
    "temp": "temperature_K",
    "h": "printed_H_Ha",
}
UNITS = {
    "time": "fs",
    "e_p": "h",
    "e_k": "h",
    "etot": "h",
    "e_tot": "h",
    "temp": "k",
    "h": "h",
}
SECTION_UNITS = {
    "xa": "angst",
    "va": "angst/fs",
    "fa": "h/au",
    "lattice": "angst",
    "stress": "gpa",
}
TEXT = {
    "en": {
        "title": "PASP native MD analysis",
        "limit": "Trajectory completeness, electronic evidence and physical convergence are separate. No equilibrium, cutoff or timestep convergence is certified.",
        "status": "Status",
        "stats": "Window statistics",
        "issues": "Issues",
        "missing": "Not supplied",
        "error": "Analysis failed",
        "exchange": "Ordinary Ep+Ek is an accounting diagnostic; thermostat/barostat exchange and extended conserved quantities require ensemble-specific evidence.",
    },
    "zh-Hans": {
        "title": "PASP 原生 MD 分析",
        "limit": "轨迹完整性、电子求解证据和物理收敛分别报告；不认证平衡、截断能或时间步长收敛。",
        "status": "状态",
        "stats": "窗口统计",
        "issues": "问题",
        "missing": "未提供",
        "error": "分析失败",
        "exchange": "普通 Ep+Ek 仅作能量记账诊断；热浴、压浴交换及扩展守恒量需要具体系综证据。",
    },
    "zh-Hant": {
        "title": "PASP 原生 MD 分析",
        "limit": "軌跡完整性、電子求解證據和物理收斂分別報告；不認證平衡、截斷能或時間步長收斂。",
        "status": "狀態",
        "stats": "視窗統計",
        "issues": "問題",
        "missing": "未提供",
        "error": "分析失敗",
        "exchange": "普通 Ep+Ek 僅作能量記帳診斷；熱浴、壓浴交換及擴展守恆量需要具體系綜證據。",
    },
}


def number(value: str) -> float:
    result = float(value.replace("D", "E").replace("d", "e"))
    if not math.isfinite(result):
        raise ValueError("nonfinite number: " + value)
    return result


def source(path: Path) -> dict:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": digest.hexdigest(),
    }


def determinant(a: list[list[float]]) -> float:
    # V = |det A|; A contains three lattice vectors in printed Angstrom units.
    return (
        a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1])
        - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
        + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0])
    )


def read_frames(path: Path):
    """Validate each frame before yielding it; final partial frames are errors."""
    current = None
    active = None
    first_identity = None
    schema = None
    first_count = None

    def finish(frame):
        nonlocal first_identity, schema, first_count
        required = {"time_fs", "Ep_Ha", "Ek_Ha", "Etot_Ha"}
        if (
            not required <= frame.keys()
            or not {"xa", "va", "fa"} <= frame["sections"].keys()
        ):
            raise ValueError(
                f"step {frame['step']}: incomplete frame; required scalar/xa/va/fa block missing"
            )
        sections = frame.pop("sections")
        ids = frame.pop("identities")
        identity = ids["xa"]
        if not identity or identity != ids["va"] or identity != ids["fa"]:
            raise ValueError(
                f"step {frame['step']}: atom count/id/species mismatch between xa/va/fa"
            )
        if len({x[0] for x in identity}) != len(identity) or sorted(
            x[0] for x in identity
        ) != list(range(1, len(identity) + 1)):
            raise ValueError(
                f"step {frame['step']}: duplicate, missing or invalid atom ids"
            )
        if first_identity is None:
            first_identity, first_count = identity, len(identity)
        if identity != first_identity:
            raise ValueError(
                f"step {frame['step']}: atom identities/order differ from initial frame"
            )
        this_schema = (
            tuple(sorted(sections)),
            "temperature_K" in frame,
            "printed_H_Ha" in frame,
        )
        if schema is None:
            schema = this_schema
        if this_schema != schema:
            raise ValueError(
                f"step {frame['step']}: missing/inconsistent optional field or lattice/stress block"
            )
        if ("lattice" in sections) != ("stress" in sections):
            raise ValueError(
                f"step {frame['step']}: variable-cell lattice/stress must both be present"
            )
        if "lattice" in sections:
            if len(sections["lattice"]) != 3 or len(sections["stress"]) != 3:
                raise ValueError(
                    f"step {frame['step']}: incomplete lattice/stress tensor"
                )
            volume = abs(determinant(sections["lattice"]))
            if not math.isfinite(volume) or volume <= 0:
                raise ValueError(
                    f"step {frame['step']}: singular/nonfinite cell volume"
                )
            frame["volume_Angstrom3"] = volume
            # Mean diagonal stress = Tr(stress)/3, not an inferred sign convention for pressure.
            frame["mean_diagonal_stress_GPa"] = (
                sum(sections["stress"][i][i] for i in range(3)) / 3
            )
        frame["atom_count"] = first_count
        frame["atom_identities"] = first_identity
        # Printed E_tot should equal E_p + E_k up to the accumulated print rounding.
        frame["energy_accounting_residual_Ha"] = (
            frame["Etot_Ha"] - frame["Ep_Ha"] - frame["Ek_Ha"]
        )
        if not math.isfinite(frame["energy_accounting_residual_Ha"]):
            raise ValueError(f"step {frame['step']}: energy accounting overflow")
        return frame

    with path.open(encoding="utf-8-sig", errors="strict") as stream:
        for line_no, raw in enumerate(stream, 1):
            if len(raw) > 16384 or "\x00" in raw:
                raise ValueError(f"line {line_no}: binary/overlong line")
            line = raw.strip()
            if not line or set(line) <= {"-"}:
                active = None
                continue
            match = STEP.fullmatch(line)
            if match:
                if current is not None:
                    yield finish(current)
                current = {
                    "step": int(match[1]),
                    "line": line_no,
                    "sections": {},
                    "identities": {},
                }
                active = None
                line = match[2] or ""
                if not line:
                    continue
            if current is None:
                raise ValueError(f"line {line_no}: expected native Step header")
            match = SECTION.fullmatch(line)
            if match:
                active = match[1].lower()
                if (
                    active in current["sections"]
                    or match[2].lower() != SECTION_UNITS[active]
                ):
                    raise ValueError(
                        f"line {line_no}: duplicate section or unsupported unit"
                    )
                current["sections"][active] = []
                current["identities"][active] = []
                continue
            if active:
                row = line.split()
                needed = 6 if active in {"xa", "va", "fa"} else 3
                if len(row) != needed:
                    raise ValueError(f"line {line_no}: malformed {active} row")
                xyz = [number(x) for x in row[:3]]
                current["sections"][active].append(xyz)
                if needed == 6:
                    species, atom = int(row[3]), int(row[5])
                    if (
                        species <= 0
                        or atom <= 0
                        or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_+-]*", row[4])
                    ):
                        raise ValueError(f"line {line_no}: invalid atom species/id")
                    current["identities"][active].append((atom, species, row[4]))
                if len(current["sections"][active]) > 1000000:
                    raise ValueError(f"line {line_no}: section exceeds atom budget")
                continue
            scalars = list(SCALAR.finditer(line))
            if not scalars or SCALAR.sub("", line).strip(" ;"):
                raise ValueError(
                    f"line {line_no}: unsupported/malformed native record: {line[:80]}"
                )
            for item in scalars:
                key = item[1].lower()
                name = NAMES[key]
                if item[2].lower() != UNITS[key] or name in current:
                    raise ValueError(
                        f"line {line_no}: duplicate scalar or unsupported unit"
                    )
                current[name] = number(item[3])
    if current is None:
        raise ValueError("no native frames found")
    yield finish(current)


def requested_input(path: Path) -> dict:
    files, values, issues = [], {}, []
    active = set()

    def visit(file, depth=0):
        file = file.resolve()
        if file in active or depth > 32 or len(files) > 128:
            raise ValueError("cyclic/over-budget input includes")
        active.add(file)
        files.append(source(file))
        in_block = False
        with file.open(encoding="utf-8-sig") as stream:
            for raw in stream:
                line = raw.split("#", 1)[0].split("!", 1)[0].strip()
                parts = line.split()
                if not parts:
                    continue
                tag = parts[0].lower()
                if tag == "%include":
                    child = line[len(parts[0]) :].strip().strip("\"'")
                    visit(file.parent / child, depth + 1)
                elif tag == "%block":
                    in_block = True
                elif tag == "%endblock":
                    in_block = False
                elif not in_block and (
                    tag.startswith("pw_md.")
                    or tag in {"dft.encut", "dft.lmd", "numberofatoms"}
                ):
                    value = " ".join(parts[1:])
                    if tag in values and values[tag] != value:
                        issues.append(
                            {"code": "duplicate_requested_setting", "setting": tag}
                        )
                    values[tag] = value
        active.remove(file)

    visit(path)
    return {
        "files": files,
        "settings": values,
        "issues": issues,
        "interpretation": "requested_only_not_runtime_effective",
    }


def read_log(path: Path, frames: list[dict]) -> dict:
    rows, graceful, failures, renormal, pending, failed_steps, protocols = (
        {},
        0,
        0,
        0,
        0,
        set(),
        [],
    )
    md = False
    duplicate_rows = 0
    with path.open(encoding="utf-8-sig") as stream:
        for line in stream:
            if "Molecular Dynamics Simulation" in line or re.search(
                r"Step\s+Time\s+Iter\s+Energy", line
            ):
                md = True
            graceful += int("PASP is finished gracefully" in line)
            if "PW_MD: self-consistent iteration failed" in line:
                failures += 1
                pending += 1
            renormal += int("LOBPCG error! Renormal" in line)
            if match := re.search(r"PASP_SCF_RESULT\s+.*?status=(\w+)", line):
                protocols.append(match[1])
            if md and (match := LOG_ROW.fullmatch(line)):
                step, time, energy = int(match[1]), number(match[2]), number(match[4])
                if pending:
                    failed_steps.add(step)
                    pending = 0
                if step in rows:
                    duplicate_rows += 1
                rows[step] = (time, energy)
    missing, mismatches = [], []
    for frame in frames:
        step = frame["step"]
        if step not in rows:
            missing.append(step)
        elif (
            abs(rows[step][0] - frame["time_fs"]) > 1e-6
            or abs(rows[step][1] - frame["Etot_Ha"]) > 1.1e-6
        ):
            mismatches.append(
                {
                    "step": step,
                    "log_time_fs": rows[step][0],
                    "trajectory_time_fs": frame["time_fs"],
                    "log_energy_Ha": rows[step][1],
                    "trajectory_energy_Ha": frame["Etot_Ha"],
                }
            )
    extras = sorted(set(rows) - {f["step"] for f in frames})
    electronic = "failure_messages_present" if failures else "no_explicit_protocol"
    if protocols and not failures:
        electronic = "explicit_result_records_present"
    return {
        "source": source(path),
        "graceful_finish_markers": graceful,
        "md_row_count": len(rows),
        "duplicate_step_rows": duplicate_rows,
        "missing_steps": missing,
        "extra_steps": extras,
        "mismatches": mismatches,
        "all_trajectory_rows_match": not (
            missing or extras or mismatches or duplicate_rows
        ),
        "SCF_failure_messages": failures,
        "SCF_failure_steps_next_md_row": sorted(failed_steps),
        "SCF_failure_unique_steps": len(failed_steps),
        "unassigned_failure_messages": pending,
        "failure_step_association": "messages preceding next printed MD row; legacy association only",
        "renormal_messages": renormal,
        "explicit_SCF_status_counts": {
            x: protocols.count(x) for x in sorted(set(protocols))
        },
        "electronic_evidence": electronic,
    }


def stats(values: list[float]) -> dict | None:
    if not values:
        return None
    # Arithmetic mean and population std: mean=sum(x)/N, std=sqrt(sum((x-mean)^2)/N).
    return {
        "count": len(values),
        "mean": statistics.fmean(values),
        "std_population": statistics.pstdev(values),
        "minimum": min(values),
        "maximum": max(values),
    }


def analyze(args) -> tuple[dict, list[dict]]:
    frames = []
    dt = args.dt_fs
    for frame in read_frames(args.trajectory):
        if frames:
            previous = frames[-1]
            delta = frame["time_fs"] - previous["time_fs"]
            if (
                frame["step"] != previous["step"] + 1
                or not math.isfinite(delta)
                or delta <= 0
            ):
                raise ValueError(
                    f"step {frame['step']}: duplicate/noncontinuous step or nonmonotonic time"
                )
            if dt is None:
                dt = delta
            if abs(delta - dt) > 1e-6:
                raise ValueError(
                    f"step {frame['step']}: time spacing differs from dt={dt} fs"
                )
        frames.append(frame)
    request = requested_input(args.input) if args.input else None
    settings = request["settings"] if request else {}
    expected = args.expected_steps
    if expected is None and "pw_md.nstep" in settings:
        expected = int(settings["pw_md.nstep"].split()[0])
    requested_dt = (
        number(settings["pw_md.dt"].split()[0]) if "pw_md.dt" in settings else None
    )
    issues = list(request["issues"]) if request else []
    observed_updates = frames[-1]["step"] - frames[0]["step"]
    if expected is not None and observed_updates != expected:
        issues.append(
            {
                "code": "requested_update_count_mismatch",
                "expected_updates": expected,
                "observed_updates": observed_updates,
            }
        )
    if requested_dt is not None and dt is not None and abs(requested_dt - dt) > 1e-6:
        issues.append(
            {
                "code": "requested_dt_mismatch",
                "requested_fs": requested_dt,
                "observed_fs": dt,
            }
        )
    if (
        "numberofatoms" in settings
        and int(settings["numberofatoms"]) != frames[0]["atom_count"]
    ):
        issues.append({"code": "requested_atom_count_mismatch"})
    start = (
        args.window_start_fs
        if args.window_start_fs is not None
        else frames[0]["time_fs"]
    )
    end = (
        args.window_end_fs if args.window_end_fs is not None else frames[-1]["time_fs"]
    )
    if start > end or start < frames[0]["time_fs"] or end > frames[-1]["time_fs"]:
        raise ValueError("statistics window outside observed interval or reversed")
    window = [f for f in frames if start <= f["time_fs"] <= end]
    if not window:
        raise ValueError("statistics window contains no sampled frames")
    keys = [
        "Ep_Ha",
        "Ek_Ha",
        "Etot_Ha",
        "temperature_K",
        "printed_H_Ha",
        "volume_Angstrom3",
        "mean_diagonal_stress_GPa",
    ]
    summaries = {key: stats([f[key] for f in window if key in f]) for key in keys}
    max_residual = max(abs(f["energy_accounting_residual_Ha"]) for f in frames)
    if max_residual > 1.6e-6:
        issues.append(
            {"code": "printed_energy_accounting_mismatch", "max_abs_Ha": max_residual}
        )
    log = read_log(args.log, frames) if args.log else None
    if log and not log["all_trajectory_rows_match"]:
        issues.append({"code": "log_trajectory_pairing_mismatch"})
    if log and log["SCF_failure_messages"]:
        issues.append({"code": "SCF_failure_messages_present"})
    if log and any(
        x.lower() not in {"converged", "success", "ok"}
        for x in log["explicit_SCF_status_counts"]
    ):
        issues.append({"code": "explicit_SCF_nonconverged_status"})
    ensemble = settings.get("pw_md.ensemble", "").split()
    ensemble = {"1": "NVE", "2": "NVT", "3": "NPH", "4": "NPT"}.get(
        ensemble[0] if ensemble else "", "unknown"
    )
    energy = {
        "ordinary_energy": "printed Ep+Ek",
        "conservation_certified": False,
        "requested_ensemble": ensemble,
        "printed_accounting_max_abs_residual_Ha": max_residual,
        "interpretation": TEXT[args.lang]["exchange"],
    }
    if ensemble == "NVE" and len(window) > 1:
        times = [f["time_fs"] / 1000 for f in window]
        energies = [f["Etot_Ha"] for f in window]
        tm, em = statistics.fmean(times), statistics.fmean(energies)
        # Least-squares slope=sum((t-tm)(E-em))/sum((t-tm)^2), in Ha/ps.
        energy["ordinary_Etot_slope_Ha_per_ps"] = math.fsum(
            (t - tm) * (e - em) for t, e in zip(times, energies)
        ) / math.fsum((t - tm) ** 2 for t in times)
        energy["ordinary_Etot_peak_to_peak_Ha"] = max(energies) - min(energies)
    complete = (
        expected is not None
        and observed_updates == expected
        and not any(x["code"].startswith("requested_") for x in issues)
    )
    report = {
        "schema": "pasp-native-md-v1",
        "language": args.lang,
        "title": TEXT[args.lang]["title"],
        "source": source(args.trajectory),
        "requested_input": request,
        "requested_controls_are_runtime_evidence": False,
        "trajectory": {
            "frame_count": len(frames),
            "initial_step": frames[0]["step"],
            "final_step": frames[-1]["step"],
            "observed_updates": observed_updates,
            "expected_updates": expected,
            "time_fs": [frames[0]["time_fs"], frames[-1]["time_fs"]],
            "dt_fs": dt,
            "atom_count": frames[0]["atom_count"],
            "atom_identities": frames[0]["atom_identities"],
            "all_atom_blocks_validated": True,
            "temperature_printed": "temperature_K" in frames[0],
            "variable_cell": "volume_Angstrom3" in frames[0],
        },
        "window": {
            "requested_start_fs": start,
            "requested_end_fs": end,
            "sample_start_fs": window[0]["time_fs"],
            "sample_end_fs": window[-1]["time_fs"],
            "inclusive": True,
            "sample_count": len(window),
            "statistics": summaries,
        },
        "energy": energy,
        "log": log,
        "status": {
            "trajectory": "complete_requested_updates"
            if complete
            else "valid_observed_interval",
            "process_completion": "graceful_marker_observed"
            if log and log["graceful_finish_markers"]
            else "not_established",
            "electronic_evidence": log["electronic_evidence"]
            if log
            else "log_not_supplied",
            "physical_convergence": "not_certified",
            "has_definite_issues": bool(issues),
        },
        "issues": issues,
        "limits": [TEXT[args.lang]["limit"]],
    }
    if any(x["code"].startswith("requested_") for x in issues):
        report["status"]["trajectory"] = "requested_controls_mismatch"
    return report, frames


def render(report: dict, lang: str) -> str:
    text = TEXT[lang]
    if "error" in report:
        return f"# {text['title']}\n\n{text['error']}: {report['error']}\n"
    rows = [
        f"# {text['title']}",
        "",
        text["limit"],
        "",
        f"## {text['status']}",
        "",
        "```json",
        json.dumps(report["status"], ensure_ascii=False, indent=2),
        "```",
        "",
        f"## {text['stats']}",
        "",
        "| Observable / unit | N | Mean | Population std | Min | Max |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for key, value in report["window"]["statistics"].items():
        if value:
            rows.append(
                f"| {key} | {value['count']} | {value['mean']:.12g} | {value['std_population']:.12g} | {value['minimum']:.12g} | {value['maximum']:.12g} |"
            )
    rows += [
        "",
        f"## {text['issues']}",
        "",
        "```json",
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False),
        "```",
        "",
    ]
    return "\n".join(rows)


def plot(frames, directory: Path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    directory.mkdir(parents=True, exist_ok=True)
    fields = [("Etot_Ha", "Total energy (Ha)", "energy")]
    if "temperature_K" in frames[0]:
        fields.append(("temperature_K", "Temperature (K)", "temperature"))
    if "volume_Angstrom3" in frames[0]:
        fields.append(("volume_Angstrom3", "Cell volume (Angstrom^3)", "volume"))
    if any((directory / (name + ".png")).exists() for _, _, name in fields):
        raise FileExistsError("plot outputs already exist")
    for key, label, name in fields:
        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.plot([f["time_fs"] / 1000 for f in frames], [f[key] for f in frames], lw=0.7)
        ax.set(xlabel="Time (ps)", ylabel=label, title="Native MD " + name)
        fig.tight_layout()
        with (directory / (name + ".png")).open("xb") as handle:
            fig.savefig(handle, format="png", dpi=180)
        plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "trajectory", type=Path, help="native trajectory text; arbitrary filename"
    )
    parser.add_argument("--log", type=Path)
    parser.add_argument(
        "--input",
        type=Path,
        help="main FDF and referenced includes; requested controls only",
    )
    parser.add_argument(
        "--expected-steps",
        type=int,
        help="expected number of updates from the initial step, including a restart interval",
    )
    parser.add_argument("--dt-fs", type=float)
    parser.add_argument("--window-start-fs", type=float)
    parser.add_argument("--window-end-fs", type=float)
    parser.add_argument("--lang", choices=list(TEXT), default="en")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--output", type=Path, help="new report file; never overwrite")
    parser.add_argument(
        "--plot-dir", type=Path, help="optional new PNG outputs; requires Matplotlib"
    )
    args = parser.parse_args()
    for name in ["dt_fs", "window_start_fs", "window_end_fs"]:
        value = getattr(args, name)
        if value is not None and (
            not math.isfinite(value) or (name == "dt_fs" and value <= 0)
        ):
            parser.error("time options must be finite; dt must be positive")
    if args.expected_steps is not None and args.expected_steps < 0:
        parser.error("--expected-steps must be nonnegative")
    if args.output and args.output.exists():
        print(
            TEXT[args.lang]["error"] + ": output already exists; never overwrite",
            file=sys.stderr,
        )
        return 1
    try:
        report, frames = analyze(args)
        if args.plot_dir:
            try:
                plot(frames, args.plot_dir)
            except (OSError, ValueError, ImportError) as exc:
                report["issues"].append(
                    {"code": "plot_output_error", "detail": str(exc)}
                )
                report["status"]["has_definite_issues"] = True
        result = 1 if report["issues"] else 0
    except (OSError, ValueError, OverflowError, ImportError) as exc:
        report = {
            "schema": "pasp-native-md-v1",
            "language": args.lang,
            "title": TEXT[args.lang]["title"],
            "error": str(exc),
            "status": {
                "trajectory": "invalid_or_unreadable",
                "electronic_evidence": "not_evaluated",
                "physical_convergence": "not_certified",
                "has_definite_issues": True,
            },
        }
        if args.trajectory.is_file():
            try:
                report["source"] = source(args.trajectory)
            except OSError:
                pass
        result = 1
    rendered = (
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.format == "json"
        else render(report, args.lang)
    )
    try:
        if args.output:
            with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(rendered)
        else:
            print(rendered, end="")
    except OSError as exc:
        print(TEXT[args.lang]["error"] + ": " + str(exc), file=sys.stderr)
        return 1
    return result


if __name__ == "__main__":
    raise SystemExit(main())
