#!/usr/bin/env python3
"""Analyze sampled PASP band or stdout EIGENVAL levels without running PASP.

Python 3.10+ and NumPy; keep the packaged plot_bands.py beside this script.
Matplotlib is needed only for plotting, not for this analysis helper.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

from plot_bands import MAX_BYTES, MAX_VALUES, number, read_bands, unit_scale

TEXT = {
    "en": {
        "title": "PASP sampled eigenvalue analysis",
        "limit": "Sampled points only; this does not establish the global Brillouin-zone gap or insulating character.",
        "fill": "Occupied count is an explicit assumption of the lowest N states at each point; fractional occupations, smearing and spin labels are not inferred.",
        "ef": "Reference split is a HOMO/LUMO diagnostic only, not a proven insulating gap.",
        "missing": "Filling is unknown; supply --occupied-bands, or --ef-hartree for a diagnostic.",
        "weight": "Printed WKE includes k-point weighting and spin/smearing conventions; it is not an occupation probability.",
        "convergence": "Convergence is not certified by an eigenvalue table; inspect the matching complete log.",
        "result": "Results",
        "notes": "Limits",
        "source": "Source",
        "unit": "Energy unit",
    },
    "zh-Hans": {
        "title": "PASP 采样本征值分析",
        "limit": "仅覆盖已有采样点；不能据此证明完整布里渊区带隙或绝缘性。",
        "fill": "占据带数是假定每个点最低 N 个态已占据；不推断分数占据、展宽或自旋标签。",
        "ef": "参考能级分界仅为 HOMO/LUMO 诊断，不是已证明的绝缘带隙。",
        "missing": "填充未知；请指定 --occupied-bands，或用 --ef-hartree 进行诊断。",
        "weight": "打印 WKE 包含 k 点权重及自旋/展宽约定，不是占据概率。",
        "convergence": "本征值表不认证收敛；需核对匹配的完整日志。",
        "result": "结果",
        "notes": "边界",
        "source": "来源",
        "unit": "能量单位",
    },
    "zh-Hant": {
        "title": "PASP 採樣本徵值分析",
        "limit": "僅涵蓋已有採樣點；不能據此證明完整布里淵區能隙或絕緣性。",
        "fill": "佔據能帶數是假定每個點最低 N 個態已佔據；不推斷分數佔據、展寬或自旋標籤。",
        "ef": "參考能級分界僅為 HOMO/LUMO 診斷，不是已證明的絕緣能隙。",
        "missing": "填充未知；請指定 --occupied-bands，或用 --ef-hartree 進行診斷。",
        "weight": "列印 WKE 包含 k 點權重及自旋/展寬慣例，不是佔據機率。",
        "convergence": "本徵值表不認證收斂；需核對匹配的完整日誌。",
        "result": "結果",
        "notes": "邊界",
        "source": "來源",
        "unit": "能量單位",
    },
}
DELIMITER = re.compile(r"^=+\s+EIGENVAL\s+=+$")
KPOINT = re.compile(r"^(\d+)\s+kpoint\(Cart\)\s+(.*)$")


def read_scf(path: Path, table: int | None = None) -> dict:
    """Read complete supported stdout EIGENVAL tables; never infer WKE filling."""
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("SCF input exceeds byte budget")
    tables, active, point, status = [], None, None, "UNKNOWN"
    total_values = 0
    with path.open(encoding="utf-8-sig", errors="strict") as stream:
        for line_no, raw in enumerate(stream, 1):
            if "\x00" in raw or len(raw) > 16384:
                raise ValueError(f"line {line_no}: binary/overlong input")
            text = raw.strip()
            if "Entering electronic step of PW-DFT" in text or text == "PASP start":
                status = "UNKNOWN"
            if match := re.match(r"PASP_SCF_RESULT\s+.*?status=(\w+)", text):
                status = match[1]
            if DELIMITER.fullmatch(text):
                if active is None:
                    active = {
                        "start_line": line_no,
                        "points": [],
                        "preceding_status": status,
                    }
                    point = None
                else:
                    if not active.pop("header", False) or not active["points"]:
                        raise ValueError(
                            f"line {line_no}: empty/missing EIGENVAL table"
                        )
                    counts = {len(p["rows"]) for p in active["points"]}
                    if (
                        len(counts) != 1
                        or 0 in counts
                        or any("reciprocal" not in p for p in active["points"])
                    ):
                        raise ValueError(
                            f"line {line_no}: partial/inconsistent EIGENVAL table"
                        )
                    active["end_line"] = line_no
                    tables.append(active)
                    active = point = None
                continue
            if active is None:
                continue
            if text == "iband  weight  eigenval(Hartree)  eigenval(eV)":
                active["header"] = True
                continue
            if not text or set(text) == {"-"}:
                continue
            if match := KPOINT.fullmatch(text):
                if int(match[1]) != len(active["points"]) + 1:
                    raise ValueError(f"line {line_no}: nonsequential k-point index")
                cart = [number(t) for t in match[2].split()]
                if len(cart) != 3:
                    raise ValueError(f"line {line_no}: malformed k point")
                point = {
                    "index": int(match[1]),
                    "cartesian": cart,
                    "line": line_no,
                    "rows": [],
                }
                active["points"].append(point)
                continue
            if text.startswith("kpoint(Reci)") and point is not None:
                point["reciprocal"] = [number(t) for t in text.split()[1:]]
                if len(point["reciprocal"]) != 3:
                    raise ValueError(f"line {line_no}: malformed reciprocal point")
                continue
            if point is None:
                raise ValueError(f"line {line_no}: expected k point")
            fields = text.split()
            if len(fields) != 4:
                body = raw.rstrip("\r\n")[12:]
                fields = [body[:4], body[4:12], body[12:28], body[28:44]]
                if body[44:].strip():
                    raise ValueError(f"line {line_no}: extra eigenvalue fields")
            try:
                index = int(fields[0])
                wke, energy, _ = [number(t.strip()) for t in fields[1:]]
            except (ValueError, IndexError) as exc:
                raise ValueError(f"line {line_no}: invalid eigenvalue row") from exc
            if index != len(point["rows"]) + 1:
                raise ValueError(f"line {line_no}: nonsequential band index")
            point["rows"].append(
                {"band": index, "energy_ha": energy, "wke": wke, "line": line_no}
            )
            total_values += 1
            if total_values > MAX_VALUES:
                raise ValueError("SCF eigenvalues exceed value budget")
    if active is not None:
        raise ValueError("truncated EIGENVAL table: missing closing delimiter")
    if not tables:
        raise ValueError("no closed stdout EIGENVAL table found")
    if table is None and len(tables) != 1:
        raise ValueError("multiple EIGENVAL tables: select --table INDEX explicitly")
    selected = 1 if table is None else table
    if not 1 <= selected <= len(tables):
        raise ValueError("table index outside available tables")
    result = tables[selected - 1]
    result.update(
        input_kind="scf",
        sampling="scf_sampled",
        table_index=selected,
        table_count=len(tables),
    )
    return result


def load(path: Path, kind="auto", table=None) -> dict:
    if kind in {"auto", "bands"}:
        try:
            data = read_bands(path)
        except ValueError:
            if kind == "bands":
                raise
        else:
            if table is not None:
                raise ValueError("--table applies only to SCF stdout")
            return {
                "input_kind": "bands",
                "sampling": "path_sampled",
                "reference_ha": data.reference_ha,
                "sha256": data.sha256,
                "points": [
                    {
                        "index": i + 1,
                        "path_distance": float(x),
                        "rows": [
                            {"band": j + 1, "energy_ha": float(e)}
                            for j, e in enumerate(row)
                        ],
                    }
                    for i, (x, row) in enumerate(zip(data.path, data.energies_ha))
                ],
            }
    return read_scf(path, table)


def analyze(
    data: dict,
    *,
    occupied_bands=None,
    ef_hartree=None,
    unit="eV",
    units_per_hartree=None,
    lang="en",
) -> dict:
    scale = unit_scale(unit, units_per_hartree)
    points = data["points"]
    nb = len(points[0]["rows"]) if points else 0
    if not points or not nb or any(len(p["rows"]) != nb for p in points):
        raise ValueError("empty/partial spectrum")
    if occupied_bands is not None and not 1 <= occupied_bands < nb:
        raise ValueError("occupied-bands must leave both occupied and empty states")
    if ef_hartree is not None and not math.isfinite(ef_hartree):
        raise ValueError("EF must be finite")
    if occupied_bands is not None and ef_hartree is not None:
        raise ValueError("choose occupied-bands or EF diagnostic")
    cutoff = data.get("reference_ha") if ef_hartree is None else ef_hartree
    mode = (
        "explicit_occupied_count"
        if occupied_bands is not None
        else "reference_diagnostic"
        if cutoff is not None
        else "filling_required"
    )
    report = {
        "schema": "pasp-sampled-eigenvalues-v1",
        "input_kind": data["input_kind"],
        "sampling": data["sampling"],
        "nk": len(points),
        "nband": nb,
        "mode": mode,
        "energy_unit": unit,
        "units_per_hartree": scale,
        "occupied_bands": occupied_bands,
        "reference_ha": cutoff,
        "preceding_scf_status": data.get("preceding_status", "UNKNOWN"),
        "gap": None,
        "notes": [TEXT[lang]["limit"], TEXT[lang]["convergence"]],
        "lang": lang,
    }
    report["notes"].append(
        TEXT[lang][
            "fill"
            if occupied_bands is not None
            else "ef"
            if cutoff is not None
            else "missing"
        ]
    )
    if data["input_kind"] == "scf":
        report["notes"].append(TEXT[lang]["weight"])
        report["table_evidence"] = {
            k: data[k] for k in ("start_line", "end_line", "table_index", "table_count")
        }
    if mode == "filling_required":
        return report
    occupied, empty, direct = [], [], []

    def edge(point, row):
        return {
            "kpoint": {k: v for k, v in point.items() if k != "rows"},
            "band": row["band"],
            "energy": row["energy_ha"] * scale,
            **{k: row[k] for k in ("line", "wke") if k in row},
        }

    for point in points:
        rows = sorted(point["rows"], key=lambda r: r["energy_ha"])
        if occupied_bands is not None:
            low, high = rows[:occupied_bands], rows[occupied_bands:]
        else:
            low = [r for r in rows if r["energy_ha"] <= cutoff]
            high = [r for r in rows if r["energy_ha"] > cutoff]
        if low:
            occupied.append(edge(point, low[-1]))
        if high:
            empty.append(edge(point, high[0]))
        if low and high:
            direct.append(
                {
                    "kpoint": point["index"],
                    "value": (high[0]["energy_ha"] - low[-1]["energy_ha"]) * scale,
                }
            )
    if not occupied or not empty:
        report["status"] = "missing_occupied_or_empty_states"
        return report
    vmax = max(e["energy"] for e in occupied)
    cmin = min(e["energy"] for e in empty)
    report["edges"] = {
        "vbm" if occupied_bands is not None else "homo": [
            e for e in occupied if e["energy"] == vmax
        ],
        "cbm" if occupied_bands is not None else "lumo": [
            e for e in empty if e["energy"] == cmin
        ],
    }
    report["status"] = (
        "sampled_gap_or_overlap" if occupied_bands is not None else "diagnostic_only"
    )
    if occupied_bands is not None:
        minimum = min(d["value"] for d in direct)
        report["gap"] = {
            "indirect": cmin - vmax,
            "minimum_direct": minimum,
            "direct_kpoint_indices": [
                d["kpoint"] for d in direct if d["value"] == minimum
            ],
            "overlap": cmin < vmax,
        }
    else:
        report["reference_diagnostic"] = {
            "sampled_homo_lumo_separation": cmin - vmax,
            "points_with_both_sides": len(direct),
        }
    return report


def markdown(report: dict) -> str:
    text = TEXT[report["lang"]]
    body = {k: v for k, v in report.items() if k != "notes"}
    return (
        f"# {text['title']}\n\n{text['result']}\n\n```json\n{json.dumps(body, ensure_ascii=False, indent=2, allow_nan=False)}\n```\n\n{text['notes']}\n\n"
        + "\n".join(f"- {note}" for note in report["notes"])
        + "\n"
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument(
        "--input-kind", choices=("auto", "bands", "scf"), default="auto"
    )
    parser.add_argument("--table", type=int)
    filling = parser.add_mutually_exclusive_group()
    filling.add_argument("--occupied-bands", type=int)
    filling.add_argument("--ef-hartree", type=float)
    parser.add_argument("--unit", default="eV")
    parser.add_argument("--units-per-hartree", type=float)
    parser.add_argument("--lang", choices=tuple(TEXT), default="en")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        data = load(args.input, args.input_kind, args.table)
        report = analyze(
            data,
            occupied_bands=args.occupied_bands,
            ef_hartree=args.ef_hartree,
            unit=args.unit,
            units_per_hartree=args.units_per_hartree,
            lang=args.lang,
        )
        report["source"] = str(args.input.resolve())
        result = (
            json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
            if args.format == "json"
            else markdown(report)
        )
        if args.output:
            with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(result)
        else:
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8")
            sys.stdout.write(result)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
