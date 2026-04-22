# -*- coding: utf-8 -*-
"""題目 ID 顯示字串、題目連結、貼文標籤。"""
from __future__ import annotations

import re
from pathlib import Path


def cpp_stem_to_share_label(stem: str) -> str:
    """將 .cpp 檔名（不含副檔名）轉成貼文用題號，例如 UVa_11413 -> UVa.11413。"""
    s = stem
    s = re.sub(r"(?i)UVa_", "UVa.", s)
    s = re.sub(r"(?i)CSES_", "CSES.", s)
    s = re.sub(r"(?i)Luogu_", "Luogu.", s)
    s = re.sub(r"(?i)LibreOJ_", "LibreOJ.", s)
    s = re.sub(r"(?i)CodeForces_", "CodeForces.", s)
    s = re.sub(r"AtCoder_", "AtCoder.", s)
    s = re.sub(r"ZeroJudge_", "ZeroJudge.", s)
    s = s.replace("_", ".")
    s = s.replace("-", " · ")
    return s


def cpp_path_outer_folder_name(cpp_path: str) -> str:
    """程式碼所在資料夾名稱（如 day-183、further）。"""
    if not cpp_path or not str(cpp_path).strip():
        return "（未知資料夾）"
    p = Path(cpp_path)
    if p.is_file():
        return p.parent.name
    return p.name


def _strip_apcs_noise(s: str) -> str:
    return re.sub(r"\b\d{4}\s*APCS\b", "", s, flags=re.I).strip()


def _describe_canonical_segment(seg: str) -> str | None:
    if not seg:
        return None
    seg = seg.strip()
    m = re.match(r"(?i)^UVa_(\d+)$", seg)
    if m:
        return f"UVa {m.group(1)}"
    m = re.match(r"(?i)^CSES_(\d+)$", seg)
    if m:
        return f"CSES {m.group(1)}"
    m = re.match(r"^AtCoder_abc(\d+)_([A-Za-z])$", seg)
    if m:
        return f"AtCoder ABC{m.group(1)} {m.group(2).upper()}"
    m = re.match(r"(?i)^ZeroJudge_([a-z])(\d+)$", seg)
    if m:
        return f"ZeroJudge {m.group(1).upper()}{m.group(2)}"
    m = re.match(r"(?i)^Luogu_(.+)$", seg)
    if m:
        return f"洛谷 {m.group(1)}"
    m = re.match(r"(?i)^LibreOJ_(\d+)$", seg)
    if m:
        return f"LibreOJ {m.group(1)}"
    m = re.match(r"(?i)^CodeForces_(.+)$", seg)
    if m:
        return f"Codeforces {m.group(1).replace('_', ' ')}"
    return None


def format_problem_source(problem_id: str) -> str:
    """將題目 ID（檔名 stem）轉為「網站與編號」顯示字串；支援正規化命名與舊檔名。"""
    pid = _strip_apcs_noise(problem_id.strip())
    if not pid:
        return problem_id.strip()

    segs = [s for s in pid.split("-") if s]
    parts: list[str] = []
    for s in segs:
        d = _describe_canonical_segment(s)
        if d:
            parts.append(d)

    if parts:
        return " · ".join(parts)

    parts = []
    zj_match = re.findall(r"\b([a-z]\d+)\b", pid, re.I)
    for m in zj_match:
        parts.append(f"ZeroJudge {m.upper()}")
    uva_match = re.findall(r"uva\s*(\d+)", pid, re.I)
    for m in uva_match:
        parts.append(f"UVa {m}")
    if re.search(r"cses", pid, re.I):
        num = re.search(r"\d+", pid)
        if num:
            parts.append(f"CSES {num.group(0)}")
    if re.search(r"luogu", pid, re.I):
        m = re.search(r"(?i)Luogu[_-]?P?(\d+)", pid)
        if m:
            parts.append(f"洛谷 P{m.group(1)}")
        else:
            parts.append("洛谷")
    if re.search(r"libreoj|loj", pid, re.I):
        num = re.search(r"\d{3,6}", pid)
        if num:
            parts.append(f"LibreOJ {num.group(0)}")
        else:
            parts.append("LibreOJ")
    if re.search(r"apcs", pid, re.I):
        year = re.search(r"20\d{2}", pid)
        parts.append(f"APCS {year.group(0) if year else ''}".strip())
    if re.search(r"atcoder|atcode", pid, re.I):
        parts.append("AtCoder")
    if re.search(r"codeforces", pid, re.I):
        m = re.search(r"(?i)CodeForces_([^-]+)", pid)
        if m:
            parts.append(f"Codeforces {m.group(1).replace('_', ' ')}")
        else:
            parts.append("Codeforces")
    if not parts:
        return problem_id.strip()
    return " · ".join(parts)


def find_problem_link(problem_id: str) -> str:
    """根據題目 ID 推測題目頁連結（正規化檔名優先，其次舊檔名）。"""
    raw = problem_id.strip()

    m = re.search(r"(?i)Luogu_(P\d+)", raw)
    if m:
        p = m.group(1).upper()
        return f"https://www.luogu.com.cn/problem/{p}"

    m = re.search(r"AtCoder_abc(\d+)_([A-Za-z])", raw)
    if m:
        a, ch = m.group(1), m.group(2).lower()
        return f"https://atcoder.jp/contests/abc{a}/tasks/abc{a}_{ch}"

    m = re.search(r"(?i)CodeForces_([^-]+)", raw)
    if m:
        s = m.group(1).strip()
        m_cf = re.match(r"(?i)^(\d+)_([A-Z][0-9A-Za-z]*)$", s)
        if m_cf:
            return f"https://codeforces.com/problemset/problem/{m_cf.group(1)}/{m_cf.group(2)}"
        m_cf = re.match(r"(?i)^(\d+)([A-Z][0-9A-Za-z]*)$", s)
        if m_cf:
            return f"https://codeforces.com/problemset/problem/{m_cf.group(1)}/{m_cf.group(2)}"
        return ""

    m = re.search(r"(?i)LibreOJ_(\d+)", raw)
    if m:
        return f"https://loj.ac/p/{m.group(1)}"

    m = re.search(r"(?i)CSES_(\d+)", raw)
    if m:
        return f"https://cses.fi/problemset/task/{m.group(1)}"

    m = re.search(r"(?i)UVa_(\d+)", raw)
    if m:
        return f"https://vjudge.net/problem/UVA-{m.group(1)}"

    m = re.search(r"(?i)ZeroJudge_([a-z])(\d+)", raw)
    if m:
        zid = (m.group(1) + m.group(2)).upper()
        return f"https://zerojudge.tw/ShowProblem?problemid={zid}"

    low = raw.lower()
    uva_match = re.search(r"uva\s*(\d+)", low)
    if uva_match:
        return f"https://vjudge.net/problem/UVA-{uva_match.group(1)}"
    zj_match = re.search(r"(?<![a-z])([a-z])\s*(\d+)(?!\d)", low)
    if zj_match and not re.search(r"zerojudge_", low):
        zid = (zj_match.group(1) + zj_match.group(2)).upper()
        return f"https://zerojudge.tw/ShowProblem?problemid={zid}"
    zj_glued = re.search(r"(?<![a-z])([a-z]\d{2,})(?![a-z0-9])", low)
    if zj_glued and "luogu" not in low and "uva" not in low:
        return f"https://zerojudge.tw/ShowProblem?problemid={zj_glued.group(1).upper()}"
    if "cses" in low:
        num = re.search(r"\d+", raw)
        if num:
            return f"https://cses.fi/problemset/task/{num.group(0)}"
    return ""
