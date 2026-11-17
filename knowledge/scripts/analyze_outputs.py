#!/usr/bin/env python3
"""Read PASP PW/PWRS text logs; summarize evidence without running PASP.

Python 3.10+, standard library only. Native output artifacts are inventoried,
never decoded. Log input is streamed; only per-stage summaries are retained.
"""

from __future__ import annotations

import argparse
import copy
import fnmatch
import json
import math
import re
import sys
from pathlib import Path

NUMBER = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?"
NUMBERS = re.compile(NUMBER)
NONFINITE = re.compile(
    r"(?<![\w.])[+-]?(?:nan(?:\([^)]*\))?|inf(?:inity)?)(?![\w.])",
    re.IGNORECASE,
)
NUMERIC_CONTEXT = re.compile(
    r"^(?:PASP_(?:SCF_RESULT|BAND_RESULT|BAND_REFERENCE|SOLVER_PROFILE|RS_SOLVER_TIMING)\b|"
    r"Total energy \(in Hartree\) is:|eband,|eband-deband,|EHub:|"
    r"total magnetism:|absolute magnetism\s*:|total\((?:Ha/a\.u\.\^3|kbar)\):)"
)
RESULT = re.compile(r"^\s*PASP_(SCF|BAND)_RESULT\b(.*)")
PAIRS = re.compile(r"([A-Za-z_][\w]*)=([^\s]+)")
ITERATION = re.compile(rf"^\s*(\d+)\s+({NUMBER})\s+({NUMBER})\s+(\d+)\s*$")
ERROR = re.compile(
    r"^\s*(?:Error in routine\b|ERROR\s+STOP\b|Fortran runtime error:|"
    r"forrtl:\s*(?:severe|error)|MPI_ABORT\b|Fatal error\b|"
    r"slurmstepd:\s*error:|sbatch:\s*error:|\[?[^\s]*\]?\s*MPI_ABORT\b)",
    re.IGNORECASE,
)
LOG_NAMES = (
    "*.log",
    "pasp.*.out",
    "pasp.*.err",
    "slurm-*.out",
    "PASP.out",
    "stdout",
    "stderr",
)
ARTIFACT_NAMES = {
    "CHGCAR": "native density; do not assume VASP format",
    "CHGCAR.restart": "native paired density provenance",
    "WAVECAR": "native wavefunction; do not assume VASP format",
    "PLUS_U_NS": "native Hubbard occupation restart",
    "DOSCAR": "native DOS output",
    "EIGENVAL": "native eigenvalue output",
    "VLOC": "native local-potential output",
    "CRTCAR": "native current output",
    "F.dat": "native forces (Ha/Bohr)",
    "cell.str": "geometry output; verify producer",
    "output_MD.dat": "native PW_MD trajectory/thermodynamic table",
    "DFT.LMD": "native DFT MD input/control; not effective-H MD",
}
LIMIT = 200
SNIFF_BYTES = 65536
PASP_CONTENT = re.compile(
    r"^\s*(?:PASP_(?:SCF_RESULT|BAND_RESULT|BAND_REFERENCE|RUN_CONFIG|SCF_ONLY|"
    r"RS_RESOURCES|RS_REPRESENTATION|RS_SOLVER_TIMING|SOLVER_PROFILE|RS_GAUSSIAN_SETUP|KPOINT)\b|"
    r"PASP start\b|PASP is finished gracefully\b|"
    r"Property Analysis and Simulation Package for materials \(PASP\)|"
    r"Total energy \(in Hartree\) is:|total time in DFT_SCF:)|"
    r"Entering electronic step of PW-DFT|Time using in DFT_SCF",
    re.MULTILINE,
)

# Human wording only. Technical keys, status codes, paths and captured log
# text stay unchanged. English is the default for both report formats.
TRANSLATIONS = {
    "NUL byte: refusing binary/non-text log": (
        "发现 NUL 字节，拒绝二进制/非文本日志",
        "發現 NUL 位元組，拒絕二進位/非文字日誌",
    ),
    "nonfinite number": ("非有限数值", "非有限數值"),
    "--output must be a report filename, not a native artifact": (
        "--output 必须使用报告文件名，不能使用原生结果文件名",
        "--output 必須使用報告檔案名稱，不能使用原生結果檔案名稱",
    ),
    "Evidence retained / total": ("保留证据数 / 总数", "保留證據數 / 總數"),
    "PASP output evidence summary": ("PASP 输出证据摘要", "PASP 輸出證據摘要"),
    "Read-only text analysis; status does not certify physical accuracy. Timers are printed values from the reporting rank; nested components must not be added.": (
        "只读文本分析；状态不认证物理精度。计时为报告 rank 的打印值，嵌套项不可相加。",
        "唯讀文字分析；狀態不認證物理精度。計時為報告 rank 的列印值，巢狀項不可相加。",
    ),
    "Outcome": ("结论", "結論"),
    "lines": ("行", "行"),
    "errors": ("错误", "錯誤"),
    "warnings": ("警告", "警告"),
    "graceful": ("正常结束标记", "正常結束標記"),
    "Stage": ("阶段", "階段"),
    "Status": ("状态", "狀態"),
    "Criterion": ("判据", "判據"),
    "Note": ("提示", "提示"),
    "last_iteration": ("最后迭代", "最後迭代"),
    "energy": ("能量", "能量"),
    "magnetization": ("磁化积分", "磁化積分"),
    "stress": ("应力", "應力"),
    "force": ("力", "力"),
    "timing": ("计时", "計時"),
    "Native file inventory (names and sizes only)": (
        "原生文件清单（仅名称与大小）",
        "原生檔案清單（僅名稱與大小）",
    ),
    "Read issues": ("读取问题", "讀取問題"),
    "Unconfirmed text candidates": ("待确认文本候选", "待確認文字候選"),
    "PASP has no required filename suffix. These files had no recognized marker in a bounded sample; select by provenance, without automatically choosing the newest file.": (
        "PASP 无固定文件后缀。有限样本内未识别的文件需按来源指定，不自动选择最新文件。",
        "PASP 無固定檔案後綴。有限樣本內未識別的檔案需按來源指定，不自動選擇最新檔案。",
    ),
    "sampled": ("已检查", "已檢查"),
    "failure_observed": ("已观察到错误或数值失败", "已觀察到錯誤或數值失敗"),
    "unconverged_observed": ("已观察到未收敛阶段", "已觀察到未收斂階段"),
    "no_stage_evidence": ("没有可识别的计算阶段证据", "沒有可識別的計算階段證據"),
    "convergence_unconfirmed": (
        "缺少明确结果，尚不能确认收敛",
        "缺少明確結果，尚不能確認收斂",
    ),
    "completion_unconfirmed": (
        "判据已满足，但后续正常结束未确认",
        "判據已滿足，但後續正常結束未確認",
    ),
    "criteria_met_and_graceful_observed": (
        "已观察到各阶段判据满足及其后正常结束",
        "已觀察到各階段判據滿足及其後正常結束",
    ),
    "legacy_criterion_met": ("旧有 SCF 判据满足", "既有 SCF 判據滿足"),
    "band_eigenvalue_criterion_met": ("能带本征值判据满足", "能帶本徵值判據滿足"),
    "unconverged": ("未收敛", "未收斂"),
    "numerical_failure": ("数值失败", "數值失敗"),
    "unknown_protocol_or_missing_result": ("协议未知或缺少结果", "協議未知或缺少結果"),
    "printed precision only; absent EHub assumed zero; verify matching input and complete log": (
        "仅核对打印精度；缺少 EHub 时假定零，需核对匹配输入和完整日志",
        "僅核對列印精度；缺少 EHub 時假定零，需核對相符輸入和完整日誌",
    ),
    "truncated total-stress matrix": ("总应力矩阵被截断", "總應力矩陣遭截斷"),
    "POSITION/FORCE block has no END marker": (
        "POSITION/FORCE 块缺少 END 标记",
        "POSITION/FORCE 區塊缺少 END 標記",
    ),
    "printed observables belong to an unconverged last iterate": (
        "打印的可观测量属于未收敛的最后迭代",
        "列印的可觀測量屬於未收斂的最後迭代",
    ),
    "no explicit result: older binary, incomplete log, or unsupported route": (
        "没有明确结果：可能是旧二进制、日志不完整或未支持的路径",
        "沒有明確結果：可能是舊二進位程式、日誌不完整或未支援的路徑",
    ),
    "invalid UTF-8 replaced": ("无效 UTF-8 字节已替换", "無效 UTF-8 位元組已替換"),
    "nonfinite numerical evidence": ("发现非有限数值证据", "發現非有限數值證據"),
    "stage inferred from changed status/complete result; no banner": (
        "无阶段标题，根据变化的状态/完整结果推断新阶段",
        "無階段標題，根據變化的狀態/完整結果推斷新階段",
    ),
    "later PASP startup has no recognized electronic stage": (
        "后续 PASP 启动缺少可识别电子阶段",
        "後續 PASP 啟動缺少可識別電子階段",
    ),
    "no graceful marker: truncated, still running, failed, or redirected output": (
        "无正常结束标记：可能截断、仍在运行、失败或输出被重定向",
        "無正常結束標記：可能截斷、仍在執行、失敗或輸出遭重新導向",
    ),
    "per-file evidence; no exit status, cross-file chronology, or physical-accuracy certification": (
        "仅为单文件证据，不含退出状态、跨文件时序或物理精度认证",
        "僅為單檔案證據，不含結束狀態、跨檔案時序或物理精度認證",
    ),
    "no recognized marker in bounded sample; may still be PASP output; specify explicitly if relevant": (
        "有限样本内无可识别标记，仍可能是 PASP 输出；相关时请明确指定",
        "有限樣本內無可識別標記，仍可能是 PASP 輸出；相關時請明確指定",
    ),
    "native density; do not assume VASP format": (
        "原生密度；不可假定 VASP 格式",
        "原生密度；不可假定 VASP 格式",
    ),
    "native paired density provenance": (
        "原生密度配对来源元数据",
        "原生密度配對來源中繼資料",
    ),
    "native wavefunction; do not assume VASP format": (
        "原生波函数；不可假定 VASP 格式",
        "原生波函數；不可假定 VASP 格式",
    ),
    "native Hubbard occupation restart": (
        "原生 Hubbard 占据重启",
        "原生 Hubbard 佔據重新啟動",
    ),
    "native DOS output": ("原生 DOS 输出", "原生 DOS 輸出"),
    "native eigenvalue output": ("原生本征值输出", "原生本徵值輸出"),
    "native local-potential output": ("原生局域势输出", "原生局域勢輸出"),
    "native current output": ("原生电流输出", "原生電流輸出"),
    "native forces (Ha/Bohr)": ("原生力（Ha/Bohr）", "原生力（Ha/Bohr）"),
    "geometry output; verify producer": (
        "几何输出；需核对生成程序",
        "幾何輸出；需核對產生程式",
    ),
    "native PW_MD trajectory/thermodynamic table": (
        "原生 PW_MD 轨迹/热力学表",
        "原生 PW_MD 軌跡/熱力學表",
    ),
    "native DFT MD input/control; not effective-H MD": (
        "原生 DFT MD 输入/控制，与 effective-H MD 区分",
        "原生 DFT MD 輸入/控制，與 effective-H MD 區分",
    ),
    "native band plot data; EF/reference requires matching log": (
        "原生能带绘图数据；EF/参考须核对匹配日志",
        "原生能帶繪圖資料；EF/參考須核對相符日誌",
    ),
    "native restart/MD artifact; producer-dependent, not decoded": (
        "原生重启/MD 文件；依赖生成程序，未解码",
        "原生重新啟動/MD 檔案；依賴產生程式，未解碼",
    ),
}
EN_EXPLANATIONS = {
    "failure_observed": "An error or numerical failure was observed",
    "unconverged_observed": "At least one stage remains unconverged",
    "no_stage_evidence": "No recognized calculation-stage evidence",
    "convergence_unconfirmed": "Missing explicit results; convergence is unconfirmed",
    "completion_unconfirmed": "Criteria met, but subsequent graceful completion is unconfirmed",
    "criteria_met_and_graceful_observed": "Stage criteria and subsequent graceful completion were observed",
    "legacy_criterion_met": "Legacy SCF criterion met",
    "band_eigenvalue_criterion_met": "Band eigenvalue criterion met",
    "unknown_protocol_or_missing_result": "Unknown protocol or missing result",
    "unconverged": "Unconverged",
    "numerical_failure": "Numerical failure",
}
DIAGNOSTICS = (
    (
        r"malformed/overflow (.+) at line (\d+)",
        "Malformed/overflow {0} at line {1}",
        "第 {1} 行的 {0} 格式错误或溢出",
        "第 {1} 行的 {0} 格式錯誤或溢位",
    ),
    (
        r"incomplete (.+) stress near line (\d+)",
        "Incomplete {0} stress near line {1}",
        "第 {1} 行附近的 {0} 应力不完整",
        "第 {1} 行附近的 {0} 應力不完整",
    ),
    (
        r"malformed force row at line (\d+)",
        "Malformed force row at line {0}",
        "第 {0} 行的力数据格式错误",
        "第 {0} 行的力資料格式錯誤",
    ),
    (r"missing path: (.+)", "Missing path: {0}", "路径不存在：{0}", "路徑不存在：{0}"),
    (
        r"binary/non-text input refused: (.+)",
        "Binary/non-text input refused: {0}",
        "拒绝二进制/非文本输入：{0}",
        "拒絕二進位/非文字輸入：{0}",
    ),
    (
        r"pseudopotential input is not an output log: (.+)",
        "Pseudopotential input is not an output log: {0}",
        "赝势输入不是输出日志：{0}",
        "贗勢輸入不是輸出日誌：{0}",
    ),
    (r"cannot scan (.+)", "Cannot scan {0}", "无法扫描 {0}", "無法掃描 {0}"),
    (r"cannot analyze (.+)", "Cannot analyze {0}", "无法分析 {0}", "無法分析 {0}"),
)


def wording(text: str, lang: str) -> str:
    if lang == "en":
        return EN_EXPLANATIONS.get(text, text)
    if text in TRANSLATIONS:
        return TRANSLATIONS[text][0 if lang == "zh-Hans" else 1]
    for pattern, _, hans, hant in DIAGNOSTICS:
        if match := re.fullmatch(pattern, text):
            parts = list(match.groups())
            if pattern == r"cannot analyze (.+)":
                for english, translations in TRANSLATIONS.items():
                    suffix = ": " + english
                    if parts[0].endswith(suffix):
                        parts[0] = (
                            parts[0][: -len(suffix)]
                            + ": "
                            + translations[0 if lang == "zh-Hans" else 1]
                        )
                        break
            return (hans if lang == "zh-Hans" else hant).format(*parts)
    return text


def localized_report(report: dict, lang: str) -> dict:
    result = copy.deepcopy(report)

    def visit(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in {"note", "reason", "kind"} and isinstance(value, str):
                    node[key] = wording(value, lang)
                elif key in {"notes", "issues"}:
                    node[key] = [wording(text, lang) for text in value]
                else:
                    visit(value)
        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(result)
    result["language"] = lang
    for log in result["logs"]:
        log["summary"] = wording(log["outcome"], lang)
    return result


def number(token: str) -> float:
    value = float(token.replace("D", "E").replace("d", "e"))
    if not math.isfinite(value):
        raise ValueError("nonfinite number")
    return value


def values(text: str) -> list[float]:
    return [number(token) for token in NUMBERS.findall(text)]


def evidence(line: int, text: str, **extra) -> dict:
    return {"line": line, "text": text.strip()[:500], **extra}


def append_event(report: dict, category: str, record: dict) -> None:
    report[category + "_count"] += 1
    if len(report[category]) < LIMIT:
        report[category].append(record)
    report["last_" + category] = record


def stage(kind: str, line: int) -> dict:
    return {
        "kind": kind,
        "start_line": line,
        "end_line": line,
        "result": {},
        "result_records": [],
        "result_record_count": 0,
        "iteration_rows": 0,
        "last_iteration": None,
        "energy_block_count": 0,
        "energy": {},
        "magnetization": {},
        "timing": {},
        "stress": {},
        "force": {},
        "notes": [],
    }


def parse_pairs(text: str) -> dict:
    parsed = {}
    for key, token in PAIRS.findall(text):
        if token in {"T", "F"}:
            parsed[key] = token == "T"
        elif re.fullmatch(NUMBER, token):
            parsed[key] = number(token)
        else:
            parsed[key] = token
    return parsed


def finish_stage(item: dict) -> None:
    status = item["result"].get("status", "UNKNOWN")
    item["observed_status"] = status
    item["convergence"] = {
        "LEGACY_CONVERGED": "legacy_criterion_met",
        "EIGENVALUES_CONVERGED": "band_eigenvalue_criterion_met",
        "MAXITER": "unconverged",
        "NUMERICAL_FAILURE": "numerical_failure",
    }.get(status, "unknown_protocol_or_missing_result")
    energy = item["energy"]
    if "total_hartree" in energy and "components" in energy:
        # +U may be enabled without an EHub line in a truncated log. An absent
        # term is explicitly an assumption; never certify the energy balance.
        hub = energy.get("ehub", {}).get("value", 0.0)
        delta = (
            sum(energy["components"]["values"]) + hub - energy["total_hartree"]["value"]
        )
        energy["sum_check"] = {
            "sum_minus_printed_hartree": delta,
            "ehub_present": "ehub" in energy,
            "note": "printed precision only; absent EHub assumed zero; verify matching input and complete log",
        }
    if "contraction" in energy:
        pair = energy["contraction"]["values"]
        energy["contraction"]["difference_hartree"] = pair[0] - pair[1]
    if item.get("stress_pending"):
        item["notes"].append("truncated total-stress matrix")
    item.pop("stress_pending", None)
    if item.pop("force_open", False):
        item["notes"].append("POSITION/FORCE block has no END marker")
    if status == "MAXITER" and energy:
        item["notes"].append(
            "printed observables belong to an unconverged last iterate"
        )
    if status == "UNKNOWN":
        item["notes"].append(
            "no explicit result: older binary, incomplete log, or unsupported route"
        )


def analyze_log(path: Path) -> dict:
    report = {
        "path": str(path),
        "bytes": path.stat().st_size,
        "lines": 0,
        "stages": [],
        "errors": [],
        "errors_count": 0,
        "warnings": [],
        "warnings_count": 0,
        "graceful": [],
        "graceful_count": 0,
        "notes": [],
    }
    current = None
    after_graceful = False
    pending_start = None
    iteration_table = False
    last_content = 0

    def ensure(kind: str, line: int, force_new: bool = False) -> dict:
        nonlocal current, after_graceful, iteration_table, pending_start
        if current is None or current["kind"] != kind or force_new or after_graceful:
            if current is not None and not after_graceful:
                current["end_line"] = max(current["start_line"], line - 1)
            current = stage(kind, line)
            report["stages"].append(current)
            iteration_table = False
        after_graceful = False
        pending_start = None
        return current

    with path.open("r", encoding="utf-8-sig", errors="replace") as stream:
        for line_no, raw in enumerate(stream, 1):
            report["lines"] = line_no
            if "\x00" in raw:
                raise ValueError("NUL byte: refusing binary/non-text log")
            if "\ufffd" in raw and "invalid UTF-8 replaced" not in report["notes"]:
                report["notes"].append("invalid UTF-8 replaced")
            text = raw.strip()
            if current is not None and not after_graceful:
                current["end_line"] = line_no
            numeric_context = NUMERIC_CONTEXT.match(text) or (
                current is not None
                and not after_graceful
                and (
                    current.get("stress_pending")
                    or (current.get("force_open") and re.match(r"\d+\s", text))
                    or (iteration_table and re.match(r"\d+\s", text))
                    or re.match(
                        r".*(?:time|calls|columns|cal H Psi).*:", text, re.IGNORECASE
                    )
                )
            )
            if numeric_context:
                invalid = bool(NONFINITE.search(text))
                try:
                    values(text)
                except ValueError:
                    invalid = True
                if invalid:
                    result_match = RESULT.match(raw)
                    if current is None:
                        ensure(result_match[1] if result_match else "UNKNOWN", line_no)
                    append_event(
                        report,
                        "errors",
                        evidence(line_no, raw, reason="nonfinite numerical evidence"),
                    )
                    last_content = line_no
                    continue
            if ERROR.search(raw) or re.match(
                r"^\s*(?:Read WAVECAR ERROR!!!|ERROR!!!)", raw
            ):
                append_event(report, "errors", evidence(line_no, raw))
                last_content = line_no
            if re.match(r"^\s*WARNING\s*:", raw, re.IGNORECASE):
                append_event(report, "warnings", evidence(line_no, raw))
            if re.match(r"^\s*PASP is finished gracefully\.?\s*$", raw):
                append_event(report, "graceful", evidence(line_no, raw))
                after_graceful = True
                iteration_table = False
                continue
            if after_graceful and text == "PASP start":
                pending_start = line_no
                last_content = line_no
                continue
            if "Entering electronic step of PW-DFT" in raw:
                kind = "NSCF" if "(NSCF)" in raw else "SCF"
                ensure(kind, line_no, True)
                iteration_table = True
                last_content = line_no
                continue
            if re.match(r"^\s*PASP_BAND_REFERENCE\b", raw):
                item = ensure("BAND", line_no, True)
                item["reference"] = evidence(line_no, raw, values=parse_pairs(raw))
                last_content = line_no
                continue
            if text.startswith("Band iterations:"):
                ensure("BAND", line_no)
                iteration_table = True
                continue
            match = RESULT.match(raw)
            if match:
                kind, payload = match.groups()
                record = parse_pairs(payload)
                item = ensure(kind, line_no)
                # With no banner, distinguish successive complete result payloads.
                # Identical duplicates remain one stage with all marker evidence.
                if (
                    "status" in record
                    and "status" in item["result"]
                    and record["status"] != item["result"]["status"]
                ) or (
                    "iterations" in record
                    and "iterations" in item["result"]
                    and any(
                        item["result"].get(key) != val for key, val in record.items()
                    )
                ):
                    item = ensure(kind, line_no, True)
                    item["notes"].append(
                        "stage inferred from changed status/complete result; no banner"
                    )
                item["result"].update(record)
                item["result_record_count"] += 1
                if len(item["result_records"]) < LIMIT:
                    item["result_records"].append(evidence(line_no, raw, values=record))
                iteration_table = False
                last_content = line_no
                continue
            if "End of electronic step of PW-DFT" in raw:
                iteration_table = False
            if current is None:
                # Some old/trimmed logs start directly with observables.
                if text.startswith(
                    (
                        "Total energy (in Hartree) is:",
                        "total(Ha/a.u.^3):",
                        "total(kbar):",
                    )
                ):
                    ensure("UNKNOWN", line_no)
                else:
                    continue
            if after_graceful:
                continue
            item = current
            if iteration_table and (match := ITERATION.match(raw)):
                row = match.groups()
                item["iteration_rows"] += 1
                item["last_iteration"] = evidence(
                    line_no,
                    raw,
                    iteration=int(row[0]),
                    ef_hartree=number(row[1]),
                    **(
                        {"max_eigenvalue_change_hartree": number(row[2])}
                        if item["kind"] == "BAND"
                        else {"eband_hartree": number(row[2])}
                    ),
                    diag_iter=int(row[3]),
                )
                last_content = line_no
            if text.startswith("Total energy (in Hartree) is:"):
                nums = values(text.split(":", 1)[1])
                item["energy_block_count"] += 1
                item["energy"] = {}
                if len(nums) == 1:
                    item["energy"]["total_hartree"] = evidence(
                        line_no, raw, value=nums[0]
                    )
                last_content = line_no
            for prefix, key, count in (
                ("eband,-deband,EH,Exc,EII,Edip:", "components", 6),
                ("EHub:", "ehub", 1),
                ("eband-deband, Ts+Epslocal+Enl+Ezeeman:", "contraction", 2),
                ("eband-deband, Ts+Epslocal+Enl:", "contraction", 2),
            ):
                if text.startswith(prefix):
                    nums = values(text[len(prefix) :])
                    if len(nums) == count:
                        item["energy"][key] = evidence(
                            line_no,
                            raw,
                            **({"value": nums[0]} if count == 1 else {"values": nums}),
                        )
                    else:
                        item["notes"].append(
                            f"malformed/overflow {key} at line {line_no}"
                        )
            for prefix, key in (
                ("total magnetism:", "total"),
                ("absolute magnetism", "absolute"),
            ):
                if text.startswith(prefix) and ":" in text:
                    nums = values(text.split(":", 1)[1])
                    if len(nums) in {1, 3}:
                        item["magnetization"][key] = evidence(line_no, raw, values=nums)
            # Only the explicitly labelled total tensor, never a component tensor.
            stress_match = re.match(r"^total\((Ha/a\.u\.\^3|kbar)\):\s*(.*)", text)
            if stress_match:
                unit, tail = stress_match.groups()
                nums = values(tail)
                item["stress"][unit] = evidence(
                    line_no, raw, rows=[nums], complete=False
                )
                item["stress_pending"] = unit
            elif item.get("stress_pending"):
                unit = item["stress_pending"]
                if re.fullmatch(rf"\s*{NUMBER}\s+{NUMBER}\s+{NUMBER}\s*", raw):
                    item["stress"][unit]["rows"].append(values(raw))
                    if len(item["stress"][unit]["rows"]) == 3:
                        item["stress"][unit]["complete"] = all(
                            len(row) == 3 for row in item["stress"][unit]["rows"]
                        )
                        item.pop("stress_pending")
                else:
                    item["notes"].append(
                        f"incomplete {unit} stress near line {line_no}"
                    )
                    item.pop("stress_pending")
            if "POSITION and FORCE END" in text:
                item["force"]["end_line"] = line_no
                item["force_open"] = False
            elif "POSITION and FORCE" in text:
                item["force"] = {
                    "start_line": line_no,
                    "atom_rows": 0,
                    "max_norm_hartree_per_bohr": 0.0,
                }
                item["force_open"] = True
            elif item.get("force_open"):
                tokens = text.split()
                if len(tokens) == 7 and tokens[0].isdigit():
                    try:
                        force = [number(x) for x in tokens[4:7]]
                    except ValueError:
                        item["notes"].append(f"malformed force row at line {line_no}")
                    else:
                        item["force"]["atom_rows"] += 1
                        item["force"]["max_norm_hartree_per_bohr"] = max(
                            item["force"]["max_norm_hartree_per_bohr"],
                            math.hypot(*force),
                        )
            # Keep each printed timer separately; never add nested components.
            if ":" in text:
                label, tail = text.split(":", 1)
                if (
                    "time" in label.lower()
                    or label.endswith(("calls", "columns"))
                    or "cal H Psi" in label
                ):
                    match = re.fullmatch(rf"\s*({NUMBER})\s*(?:s|seconds)?\s*", tail)
                    if match:
                        item["timing"][label.strip()] = evidence(
                            line_no, raw, value=number(match[1])
                        )
            if re.match(r"^\s*(PASP_SOLVER_PROFILE|PASP_RS_SOLVER_TIMING)\b", raw):
                item["timing"][text.split()[0]] = evidence(
                    line_no, raw, values=parse_pairs(text)
                )
    if pending_start is not None:
        item = ensure("UNKNOWN", pending_start, True)
        item["end_line"] = report["lines"]
        item["notes"].append("later PASP startup has no recognized electronic stage")
    for item in report["stages"]:
        finish_stage(item)
    statuses = [item["observed_status"] for item in report["stages"]]
    if report["errors_count"] or "NUMERICAL_FAILURE" in statuses:
        report["outcome"] = "failure_observed"
    elif "MAXITER" in statuses:
        report["outcome"] = "unconverged_observed"
    elif not report["stages"]:
        report["outcome"] = "no_stage_evidence"
    elif any(
        item["convergence"] == "unknown_protocol_or_missing_result"
        for item in report["stages"]
    ):
        report["outcome"] = "convergence_unconfirmed"
    elif not report["graceful"] or report["last_graceful"]["line"] < last_content:
        report["outcome"] = "completion_unconfirmed"
    else:
        report["outcome"] = "criteria_met_and_graceful_observed"
    if not report["graceful_count"] and report["lines"]:
        report["notes"].append(
            "no graceful marker: truncated, still running, failed, or redirected output"
        )
    report["notes"].append(
        "per-file evidence; no exit status, cross-file chronology, or physical-accuracy certification"
    )
    return report


def artifact_kind(path: Path) -> str | None:
    if path.name in ARTIFACT_NAMES:
        return ARTIFACT_NAMES[path.name]
    if path.name.endswith(".bands"):
        return "native band plot data; EF/reference requires matching log"
    if path.name.startswith(("WAVECAR_", "PW_MD.")):
        return "native restart/MD artifact; producer-dependent, not decoded"
    return None


def discover(
    paths: list[Path], recursive: bool
) -> tuple[list[Path], list[dict], list[dict], list[str]]:
    logs, artifacts, uncertain, issues = {}, {}, {}, []
    for requested in paths:
        if not requested.exists():
            issues.append(f"missing path: {requested}")
            continue
        candidates = (
            requested.rglob("*")
            if requested.is_dir() and recursive
            else (requested.iterdir() if requested.is_dir() else [requested])
        )
        try:
            for candidate in candidates:
                if candidate.is_symlink() or not candidate.is_file():
                    continue
                resolved = candidate.resolve()
                kind = artifact_kind(candidate)
                if kind:
                    artifacts[str(resolved)] = {
                        "path": str(resolved),
                        "bytes": candidate.stat().st_size,
                        "kind": kind,
                    }
                else:
                    # Output names/suffixes are unconstrained. Probe content,
                    # never stream an arbitrary directory file just by its name.
                    with candidate.open("rb") as stream:
                        sample = stream.read(SNIFF_BYTES)
                    controls = sum(
                        byte < 32 and byte not in (9, 10, 13) for byte in sample
                    )
                    binary = b"\x00" in sample or controls > max(4, len(sample) // 100)
                    if binary:
                        if requested.is_file():
                            issues.append(f"binary/non-text input refused: {resolved}")
                        continue
                    if re.search(rb"<(?:UPF|PP_HEADER)\b", sample, re.IGNORECASE):
                        if requested.is_file():
                            issues.append(
                                f"pseudopotential input is not an output log: {resolved}"
                            )
                        continue
                    text = sample.decode("utf-8-sig", errors="replace")
                    recognized = PASP_CONTENT.search(text) or any(
                        ERROR.search(row) for row in text.splitlines()
                    )
                    if requested.is_file() or recognized:
                        logs[str(resolved)] = resolved
                    else:
                        uncertain[str(resolved)] = {
                            "path": str(resolved),
                            "bytes": candidate.stat().st_size,
                            "sampled_bytes": len(sample),
                            "filename_hint": any(
                                fnmatch.fnmatchcase(candidate.name, pattern)
                                for pattern in LOG_NAMES
                            ),
                            "reason": "no recognized marker in bounded sample; may still be PASP output; specify explicitly if relevant",
                        }
        except OSError as exc:
            issues.append(f"cannot scan {requested}: {exc}")
    return (
        [logs[key] for key in sorted(logs)],
        [artifacts[key] for key in sorted(artifacts)],
        [uncertain[key] for key in sorted(uncertain)],
        issues,
    )


def markdown(report: dict, lang: str = "en") -> str:
    def t(text):
        return wording(text, lang)

    rows = [
        "# " + t("PASP output evidence summary"),
        "",
        t(
            "Read-only text analysis; status does not certify physical accuracy. Timers are printed values from the reporting rank; nested components must not be added."
        ),
        "",
    ]
    for log in report["logs"]:
        rows += [
            f"## {log['path']}",
            "",
            f"{t('Outcome')}: `{log['outcome']}` — {t(log['outcome'])}; {log['lines']} {t('lines')}; {t('errors')}: {log['errors_count']}; {t('graceful')}: {log['graceful_count']}.",
            "",
        ]
        for index, item in enumerate(log["stages"], 1):
            rows += [
                f"### {t('Stage')} {index}: {item['kind']} ({t('lines')} {item['start_line']}–{item['end_line']})",
                "",
                f"{t('Status')}: `{item['observed_status']}`; {t('Criterion')}: {t(item['convergence'])}.",
                "",
            ]
            for record in item["result_records"]:
                rows.append(f"- L{record['line']}: `{record['text']}`")
            for key in (
                "last_iteration",
                "energy",
                "magnetization",
                "stress",
                "force",
                "timing",
            ):
                if item[key]:
                    rows += [
                        "",
                        f"{t(key)}:",
                        "",
                        "```json",
                        json.dumps(
                            item[key], ensure_ascii=False, indent=2, allow_nan=False
                        ),
                        "```",
                    ]
            for note in item["notes"]:
                rows += ["", f"{t('Note')}: {note}"]
            rows.append("")
        for category in ("errors", "warnings", "graceful"):
            for record in log[category]:
                rows.append(f"- {t(category)} L{record['line']}: `{record['text']}`")
            if log[category + "_count"] > LIMIT:
                rows.append(
                    f"- {t(category)} — {t('Evidence retained / total')}: {LIMIT}/{log[category + '_count']}"
                )
        rows += ["", *[f"{t('Note')}: {note}" for note in log["notes"]], ""]
    if report["artifacts"]:
        rows += ["## " + t("Native file inventory (names and sizes only)"), ""]
        rows.extend(
            f"- `{row['path']}`: {row['bytes']} bytes; {row['kind']}"
            for row in report["artifacts"]
        )
    if report["issues"]:
        rows += [
            "",
            "## " + t("Read issues"),
            "",
            *[f"- {issue}" for issue in report["issues"]],
        ]
    if report["candidates"]:
        rows += [
            "",
            "## " + t("Unconfirmed text candidates"),
            "",
            t(
                "PASP has no required filename suffix. These files had no recognized marker in a bounded sample; select by provenance, without automatically choosing the newest file."
            ),
            "",
        ]
        rows.extend(
            f"- `{row['path']}`: {row['bytes']} bytes; {t('sampled')} {row['sampled_bytes']} bytes"
            for row in report["candidates"]
        )
    return "\n".join(rows) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths", type=Path, nargs="+", help="explicit text logs or directories"
    )
    parser.add_argument(
        "--recursive", action="store_true", help="explicitly scan subdirectories"
    )
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument(
        "--lang",
        choices=("en", "zh-Hans", "zh-Hant"),
        default="en",
        help="report language: English (default), Simplified Chinese, Traditional Chinese",
    )
    parser.add_argument(
        "--output", type=Path, help="create a NEW user-chosen report; never overwrite"
    )
    args = parser.parse_args(argv)
    logs, artifacts, candidates, issues = discover(args.paths, args.recursive)
    report = {
        "schema_version": 1,
        "logs": [],
        "artifacts": artifacts,
        "candidates": candidates,
        "issues": issues,
    }
    for log in logs:
        try:
            report["logs"].append(analyze_log(log))
        except (OSError, ValueError) as exc:
            issues.append(f"cannot analyze {log}: {exc}")
    report = localized_report(report, args.lang)
    rendered = (
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.format == "json"
        else markdown(report, args.lang)
    )
    if args.output:
        # Exclusive creation also refuses an input path, symlink, or native file.
        if artifact_kind(args.output):
            parser.error(
                wording(
                    "--output must be a report filename, not a native artifact",
                    args.lang,
                )
            )
        try:
            with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(rendered)
        except OSError as exc:
            label = {
                "en": "Cannot create --output",
                "zh-Hans": "无法创建 --output",
                "zh-Hant": "無法建立 --output",
            }[args.lang]
            parser.error(f"{label}: {exc}")
    else:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(rendered)
    return 2 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
