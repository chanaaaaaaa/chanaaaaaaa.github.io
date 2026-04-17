#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CodeLib GitHub Pages 建置腳本
掃描 CodeLib/code 內所有題目，為每題產生解題頁面（含題解、時間複雜度），並在每頁附上隨機的其他題目連結。
輸出至 chanaaaaaaa.github.io/coding

題目檔名建議與 CodeLib 正規化規則一致：
UVa_{num}、CSES_{num}、AtCoder_abc{場次}_{題目}、ZeroJudge_{小寫字母}{數字}、
Luogu_{題號字串}（如 Luogu_P1234)、LibreOJ_{num}；複合題以「-」連接多個片段。
"""

from __future__ import annotations

import os
import re
import json
import random
import html
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# 預設路徑
DEFAULT_CODELIB = os.path.join(os.path.expanduser("~"), "Downloads", "git", "CodeLib", "code")
ALT_CODELIB = os.path.join(os.path.expanduser("~"), "Downloads", "CodeLib", "code")
DEFAULT_OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)))  # coding/ 目錄

PAGE_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - CodeLib 題解</title>
    <link rel="stylesheet" href="../styles.css">
    <link rel="stylesheet" href="../vendor/prism-tomorrow.min.css">
    <script>
      MathJax = {{
        tex: {{
          inlineMath: [['\\\\(' , '\\\\\\)']],
          displayMath: [['\\\\[', '\\\\\\]']]
        }}
      }};
    </script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" async></script>
</head>
<body>
    <div class="page-wrapper">
    <header>
        <a href="../index.html" class="back-link">← 返回題目列表</a>
        <h1>{title}</h1>
        <p class="subtitle">題目編號：{problem_id}</p>
        {problem_link_html}
    </header>

    <div class="content-card">
    <h2>題目大意</h2>
    <p>{summary_html}</p>

    <h2>題解</h2>
    <p>{solution_html}</p>

    <h2>時間複雜度</h2>
    <p>{complexity_html}</p>

    <h2>程式碼</h2>
    <pre class="code-block language-cpp"><code>{code_html}</code></pre>
    </div>

    <div class="other-problems">
        <h3>其他題目</h3>
        <p>{other_links_html}</p>
    </div>

    <footer>
        LibOfManyCodes · 程式競賽題解
    </footer>
    </div>
</body>
</html>
'''


def extract_from_code(code: str, problem_id: str) -> tuple:
    """嘗試從程式碼註解中擷取題解與時間複雜度"""
    solution = ""
    complexity = ""

    # 題解：// 題解: 或 /* 題解: 或 // 解法:
    for pattern in [
        r'//\s*題解\s*[：:]\s*(.+?)(?:\n|$)',
        r'/\*\s*題解\s*[：:]\s*(.+?)\s*\*/',
        r'//\s*解法\s*[：:]\s*(.+?)(?:\n|$)',
    ]:
        m = re.search(pattern, code, re.DOTALL)
        if m:
            solution = m.group(1).strip()
            break

    # 時間複雜度：// 時間複雜度: O(...) 或 O(n) 等
    for pattern in [
        r'//\s*時間複雜度\s*[：:]\s*(.+?)(?:\n|$)',
        r'/\*\s*時間複雜度\s*[：:]\s*(.+?)\s*\*/',
        r'//\s*複雜度\s*[：:]\s*(.+?)(?:\n|$)',
        r'//\s*Time\s*[Cc]omplexity\s*[：:]\s*(.+?)(?:\n|$)',
        r'//\s*O\s*\(\s*[^)]+\s*\)',
    ]:
        m = re.search(pattern, code, re.DOTALL)
        if m:
            complexity = m.group(1).strip() if m.lastindex else m.group(0).strip()
            break

    return solution or "（請自行補充）", complexity or "（請自行補充）"


def cpp_stem_to_share_label(stem: str) -> str:
    """
    將 .cpp 檔名（不含副檔名）轉成貼文用題號，例如 UVa_11413 -> UVa.11413。
    """
    s = stem
    s = re.sub(r"(?i)UVa_", "UVa.", s)
    s = re.sub(r"(?i)CSES_", "CSES.", s)
    s = re.sub(r"(?i)Luogu_", "Luogu.", s)
    s = re.sub(r"(?i)LibreOJ_", "LibreOJ.", s)
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


def strip_pragma_lines(code: str) -> str:
    """建置 HTML 時略過所有 `#pragma ...` 行（不寫入題解頁程式碼區塊）。"""
    out = []
    for line in code.splitlines(keepends=True):
        if line.lstrip().startswith("#pragma"):
            continue
        out.append(line)
    return "".join(out)


def highlight_cpp(code: str) -> str:
    """
    建置時進行 C++ 語法高亮，輸出 Prism 相容的 token class，
    無需依賴 JavaScript，確保顏色一定顯示。
    """
    # 依序處理：先保護字串與註解，再高亮關鍵字等
    tokens = []
    i = 0
    n = len(code)

    def esc(s):
        return html.escape(s)

    CPP_KEYWORDS = {
        'alignas', 'alignof', 'asm', 'auto', 'bool', 'break', 'case', 'catch',
        'char', 'class', 'const', 'constexpr', 'const_cast', 'continue', 'decltype',
        'default', 'delete', 'do', 'double', 'dynamic_cast', 'else', 'enum',
        'explicit', 'export', 'extern', 'false', 'float', 'for', 'friend', 'goto',
        'if', 'inline', 'int', 'long', 'mutable', 'namespace', 'new', 'noexcept',
        'nullptr', 'operator', 'override', 'private', 'protected', 'public',
        'register', 'reinterpret_cast', 'return', 'short', 'signed', 'sizeof',
        'static', 'static_assert', 'static_cast', 'struct', 'switch', 'template',
        'this', 'thread_local', 'throw', 'true', 'try', 'typedef', 'typeid',
        'typename', 'union', 'unsigned', 'using', 'virtual', 'void', 'volatile',
        'wchar_t', 'while', 'co_await', 'co_return', 'co_yield', 'concept',
        'consteval', 'constinit', 'import', 'module', 'requires',
    }

    while i < n:
        # 雙引號字串
        if code[i] == '"':
            j = i + 1
            while j < n and (code[j] != '"' or (j > 0 and code[j - 1] == '\\')):
                if code[j] == '\\':
                    j += 2
                else:
                    j += 1
            if j < n:
                j += 1
            tokens.append(f'<span class="token string">{esc(code[i:j])}</span>')
            i = j
            continue
        # 單引號字元
        if code[i] == "'":
            j = i + 1
            while j < n and (code[j] != "'" or (j > 0 and code[j - 1] == '\\')):
                if code[j] == '\\':
                    j += 2
                else:
                    j += 1
            if j < n:
                j += 1
            tokens.append(f'<span class="token string">{esc(code[i:j])}</span>')
            i = j
            continue
        # 區塊註解 /* */
        if i + 1 < n and code[i:i + 2] == '/*':
            j = code.find('*/', i + 2)
            j = j + 2 if j >= 0 else n
            tokens.append(f'<span class="token comment">{esc(code[i:j])}</span>')
            i = j
            continue
        # 行註解 //
        if i + 1 < n and code[i:i + 2] == '//':
            j = code.find('\n', i + 2)
            j = n if j < 0 else j
            tokens.append(f'<span class="token comment">{esc(code[i:j])}</span>')
            i = j
            continue
        # 預處理 #include 等
        if code[i] == '#' and (i == 0 or code[i - 1] == '\n'):
            j = i + 1
            while j < n and code[j] in ' \t':
                j += 1
            while j < n and (code[j].isalnum() or code[j] in '_'):
                j += 1
            tokens.append(f'<span class="token directive">{esc(code[i:j])}</span>')
            i = j
            continue
        # 數字
        if code[i].isdigit():
            j = i
            while j < n and (code[j].isdigit() or code[j] in '.xXaAbBcCdDeEfF'):
                j += 1
            tokens.append(f'<span class="token number">{esc(code[i:j])}</span>')
            i = j
            continue
        # 識別符與關鍵字
        if code[i].isalpha() or code[i] == '_':
            j = i
            while j < n and (code[j].isalnum() or code[j] == '_'):
                j += 1
            word = code[i:j]
            if word in CPP_KEYWORDS:
                tokens.append(f'<span class="token keyword">{esc(word)}</span>')
            else:
                tokens.append(esc(word))
            i = j
            continue
        # 其他字元
        tokens.append(esc(code[i]))
        i += 1

    return ''.join(tokens)


def _strip_apcs_noise(s: str) -> str:
    """檔名整理時會刪除 YYYYAPCS；若舊資料仍含此片段，顯示時可忽略。"""
    return re.sub(r"\b\d{4}\s*APCS\b", "", s, flags=re.I).strip()


def _describe_canonical_segment(seg: str) -> str | None:
    """
    辨識單一正規化片段（不含 '-'）：
    UVa_123、CSES_45、AtCoder_abc208_E、ZeroJudge_d188、Luogu_P1234、LibreOJ_2185
    """
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
    return None


def format_problem_source(problem_id: str) -> str:
    """將題目 ID（檔名 stem）轉為「網站與編號」顯示字串；支援正規化命名與舊檔名。"""
    pid = _strip_apcs_noise(problem_id.strip())
    if not pid:
        return problem_id.strip()

    # 正規化：以 '-' 分段（ZeroJudge_d188-UVa_11342）
    segs = [s for s in pid.split("-") if s]
    parts: list[str] = []
    for s in segs:
        d = _describe_canonical_segment(s)
        if d:
            parts.append(d)

    if parts:
        return " · ".join(parts)

    # --- 舊版／未正規化檔名 fallback ---
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
    if not parts:
        return problem_id.strip()
    return " · ".join(parts)


def find_problem_link(problem_id: str) -> str:
    """根據題目 ID 推測題目頁連結（正規化檔名優先，其次舊檔名）。"""
    raw = problem_id.strip()
    pid = raw

    # 洛谷 Luogu_P1234
    m = re.search(r"(?i)Luogu_(P\d+)", raw)
    if m:
        p = m.group(1).upper()
        return f"https://www.luogu.com.cn/problem/{p}"

    # AtCoder AtCoder_abc208_E
    m = re.search(r"AtCoder_abc(\d+)_([A-Za-z])", raw)
    if m:
        a, ch = m.group(1), m.group(2).lower()
        return f"https://atcoder.jp/contests/abc{a}/tasks/abc{a}_{ch}"

    # LibreOJ LibreOJ_2185
    m = re.search(r"(?i)LibreOJ_(\d+)", raw)
    if m:
        return f"https://loj.ac/p/{m.group(1)}"

    # CSES CSES_1643
    m = re.search(r"(?i)CSES_(\d+)", raw)
    if m:
        return f"https://cses.fi/problemset/task/{m.group(1)}"

    # UVa UVa_1234（複合名稱中亦可能出現）
    m = re.search(r"(?i)UVa_(\d+)", raw)
    if m:
        return f"https://vjudge.net/problem/UVA-{m.group(1)}"

    # ZeroJudge ZeroJudge_d188
    m = re.search(r"(?i)ZeroJudge_([a-z])(\d+)", raw)
    if m:
        zid = (m.group(1) + m.group(2)).upper()
        return f"https://zerojudge.tw/ShowProblem?problemid={zid}"

    # --- 舊檔名 fallback（小寫比對）---
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


def format_text_for_display(text: str) -> str:
    """將純文字轉為 HTML 安全顯示（含換行與 MathJax 支援）"""
    if not text or not text.strip():
        return ""
    return html.escape(text).replace('\n', '<br>')


def load_meta(meta_path: Path) -> dict:
    """載入 meta.json（題解、時間複雜度）"""
    if not meta_path.exists():
        return {}
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_problems(problems_path: Path) -> list:
    """載入 data/problems.json"""
    if not problems_path.exists():
        return []
    try:
        with open(problems_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("problems", [])
    except Exception:
        return []


def safe_id_from_url(url: str) -> str:
    """從 url（如 problems/Atcoder208E.html）擷取 safe_id"""
    if "/" in url:
        url = url.split("/")[-1]
    return url.replace(".html", "") if url.endswith(".html") else url


def collect_problems(code_dir: str) -> list:
    """掃描 code 目錄內所有 .cpp 檔，每個檔案以檔名（不含 .cpp）作為題目 ID 建立一題"""
    code_path = Path(code_dir)
    if not code_path.exists():
        return []

    problems = []
    seen_safe_ids = {}

    for cpp_file in sorted(code_path.rglob("*.cpp")):
        if cpp_file.name.endswith('.o') or 'obj' in str(cpp_file).lower():
            continue

        # 題目 ID = 檔名（不含 .cpp）
        problem_id = cpp_file.stem

        try:
            with open(cpp_file, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()
        except Exception:
            code = "// 無法讀取程式碼"

        base_safe = re.sub(r'[^\w\s-]', '', problem_id).strip().replace(' ', '-')
        if not base_safe:
            base_safe = "p"
        base_safe = base_safe[:50]

        # 檔名可能重複（如多個 c.cpp），需確保 safe_id 唯一
        if base_safe not in seen_safe_ids:
            seen_safe_ids[base_safe] = 0
        seen_safe_ids[base_safe] += 1
        safe_id = base_safe if seen_safe_ids[base_safe] == 1 else f"{base_safe}-{seen_safe_ids[base_safe]}"

        solution, complexity = extract_from_code(code, problem_id)

        problems.append({
            "id": problem_id,
            "safe_id": safe_id,
            "title": problem_id,
            "code": code,
            "cpp_path": str(cpp_file.resolve()),
            "link": find_problem_link(problem_id),
            "solution": solution,
            "complexity": complexity,
        })

    return problems


def merge_with_existing(
    scanned_problems: list,
    existing_problems: list,
    existing_meta: dict,
) -> tuple:
    """
    比對掃描結果與現有 problems.json、meta.json。
    - 已出現（id + safe_id 在 problems.json 中）：保留現有資訊，不編輯
    - 未曾出現：新增至 problems（僅 id/title/url）與 meta（預填 complexity/type/difficulty、summary/content/description 空字串，以及可從註解擷取之 solution）
    回傳 (merged_problems, merged_meta)
    """
    # 建立現有題目的索引：(id, safe_id) -> 完整 entry
    existing_by_key = {}
    for p in existing_problems:
        sid = safe_id_from_url(p.get("url", ""))
        existing_by_key[(p.get("id", ""), sid)] = p

    merged_problems = []
    merged_meta = dict(existing_meta)
    new_count = 0

    for p in scanned_problems:
        key = (p["id"], p["safe_id"])
        if key in existing_by_key:
            # 已存在：保留現有 entry，不編輯
            merged_problems.append(existing_by_key[key])
        else:
            # 未曾出現：僅新增列表必要欄位（type/difficulty/description 由 meta 或預設推導，不在此預填）
            new_entry = {
                "id": p["id"],
                "title": p["title"],
                "url": f"problems/{p['safe_id']}.html",
            }
            merged_problems.append(new_entry)
            new_count += 1

            # 僅當 meta 中尚無此 id 時才新增（預填與掃描結果；summary/content/description 仍由使用者補）
            if p["id"] not in merged_meta and p["safe_id"] not in merged_meta:
                new_meta = {
                    "complexity": p.get("complexity", "（請自行補充）"),
                    "type": "其他",
                    "difficulty": 3,
                    "summary": "",
                    "content": "",
                    "description": "",
                }
                sol = (p.get("solution") or "").strip()
                if sol and sol != "（請自行補充）":
                    new_meta["solution"] = sol
                merged_meta[p["id"]] = new_meta

    # 保留孤兒題目（在 problems.json 但無對應 cpp）
    scanned_keys = {(p["id"], p["safe_id"]) for p in scanned_problems}
    for p in existing_problems:
        sid = safe_id_from_url(p.get("url", ""))
        if (p.get("id", ""), sid) not in scanned_keys:
            merged_problems.append(p)

    return merged_problems, merged_meta, new_count


def build_pages(
    scanned_problems: list,
    merged_problems: list,
    output_dir: str,
    meta: dict,
    num_links: int = 6,
):
    """
    產生各題目頁面與 index。
    - 已存在的 problems/{safe_id}.html 不覆寫；僅新建檔時寫入（程式碼為目前掃描內容）。
    - 題目大意／題解／複雜度僅來自 meta.json，不從 .cpp 註解自動帶入。
    回傳本次新建的題目頁數量。
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "problems").mkdir(exist_ok=True)
    (out / "data").mkdir(exist_ok=True)

    # 僅對有程式碼的 scanned 題目產生 HTML；已存在的 .html 不覆寫
    written = 0
    share_snapshots: list[tuple[str, str]] = []  # (外層資料夾名, 貼文題號標籤)
    for i, p in enumerate(scanned_problems):
        html_path = out / "problems" / f"{p['safe_id']}.html"
        if html_path.is_file():
            continue

        # 題目文字僅依 meta.json（不從程式註解 extract 回填 summary/solution/complexity）
        m = meta.get(p["id"], {}) or meta.get(p["safe_id"], {})
        if not isinstance(m, dict):
            m = {}
        content = m.get("content") or ""
        if content:
            parts = content.split("\n---\n", 1)
            summary = parts[0].strip() if parts[0].strip() else ""
            solution = (
                parts[1].strip()
                if len(parts) > 1 and parts[1].strip()
                else (m.get("solution") or "")
            )
        else:
            summary = m.get("summary") or m.get("description") or ""
            solution = m.get("solution") or ""
        complexity = m.get("complexity") or "（請自行補充）"

        others = [x for j, x in enumerate(scanned_problems) if j != i]
        random.shuffle(others)
        links = others[:num_links]

        other_links_html = " ".join(
            f'<a href="{x["safe_id"]}.html" class="problem-link">{html.escape(x["title"])}</a>'
            for x in links
        )

        problem_link_html = ""
        if p.get("link"):
            problem_link_html = f'<p><a href="{p["link"]}" target="_blank" rel="noopener">題目連結（原題／評測）</a></p>'

        summary_html = format_text_for_display(summary) or "（請自行查閱題目描述）"
        solution_html = format_text_for_display(solution) or "（請自行補充）"
        complexity_html = html.escape(complexity)

        code_html = highlight_cpp(strip_pragma_lines(p["code"]))
        html_content = PAGE_TEMPLATE.format(
            title=html.escape(p["title"]),
            problem_id=html.escape(p["id"]),
            problem_link_html=problem_link_html,
            summary_html=summary_html,
            solution_html=solution_html,
            complexity_html=complexity_html,
            code_html=code_html,
            other_links_html=other_links_html,
        )

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        written += 1
        cpp_p = p.get("cpp_path") or ""
        print(f"來源 .cpp: {cpp_p}")
        print(f"新建 .html: {html_path.resolve()}")
        print()
        day_folder = cpp_path_outer_folder_name(cpp_p)
        share_label = cpp_stem_to_share_label(p["id"])
        share_snapshots.append((day_folder, share_label))

    if share_snapshots:
        print("=" * 52)
        print("【每日貼文範本】以下為本次新建題目；括號內請手動補充")
        print("=" * 52)
        print()
        print(f"每日亂捲直到跟皮卡丘一樣⚡️ {day_folder}")
        for day_folder, label in share_snapshots:
            print("-")
            print(f"->{label} - （題名待補）")
            print("（待補）")
        print("-")
        print("https://chanaaaaaaa.github.io/coding/index.html")
        print("https://github.com/chanaaaaaaa/CodeLib")
        print()

    # 依類型與難度分組排序（merged_problems 已有 type、difficulty）
    TYPE_ORDER = ["圖論", "DP", "貪心", "排序", "搜尋", "數學", "字串", "資料結構", "模擬", "其他"]
    DIFFICULTY_ORDER = {1: "入門", 2: "簡單", 3: "中等", 4: "困難", 5: "進階"}

    def get_type(p):
        t = p.get("type")
        if t:
            return t
        m = meta.get(p["id"], {}) or meta.get(safe_id_from_url(p.get("url", "")), {})
        return m.get("type", "其他") if isinstance(m, dict) else "其他"

    def get_difficulty(p):
        d = p.get("difficulty")
        if d is not None:
            return int(d) if isinstance(d, (int, float)) else 3
        m = meta.get(p["id"], {}) or meta.get(safe_id_from_url(p.get("url", "")), {})
        d = m.get("difficulty") if isinstance(m, dict) else None
        return int(d) if isinstance(d, (int, float)) else 3

    grouped = {}
    for p in merged_problems:
        t = get_type(p)
        d = get_difficulty(p)
        if t not in grouped:
            grouped[t] = []
        grouped[t].append((d, p))

    for t in grouped:
        grouped[t].sort(key=lambda x: (x[0], x[1]["id"]))

    problem_list = []
    for t in TYPE_ORDER:
        if t in grouped:
            for d, p in grouped[t]:
                problem_list.append({
                    "id": p["id"],
                    "title": p["title"],
                    "url": p.get("url", ""),
                    "type": t,
                    "difficulty": d,
                })

    # 未在 TYPE_ORDER 的類型放最後
    for t in sorted(grouped.keys()):
        if t not in TYPE_ORDER:
            for d, p in grouped[t]:
                problem_list.append({
                    "id": p["id"],
                    "title": p["title"],
                    "url": p.get("url", ""),
                    "type": t,
                    "difficulty": d,
                })

    with open(out / "data" / "problems.json", "w", encoding="utf-8") as f:
        json.dump({"problems": problem_list}, f, ensure_ascii=False, indent=2)

    index_html = '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>程式競賽題解 - CodeLib</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <h1>程式競賽題解</h1>
        <p class="subtitle">LibOfManyCodes - 依類型與難度分類</p>
    </header>
'''
    current_type = None
    for pl in problem_list:
        if pl["type"] != current_type:
            if current_type is not None:
                index_html += '        </ul>\n    </section>\n'
            current_type = pl["type"]
            index_html += f'    <section class="problem-section">\n'
            index_html += f'        <h2 class="section-title">{html.escape(current_type)}</h2>\n'
            index_html += f'        <ul class="problem-list">\n'
        diff_label = DIFFICULTY_ORDER.get(pl["difficulty"], str(pl["difficulty"]))
        source_str = format_problem_source(pl["id"])
        index_html += f'            <li><a href="{pl["url"]}" class="problem-title">{html.escape(pl["title"])}</a><span class="problem-source">{html.escape(source_str)}</span><span class="difficulty-badge">{html.escape(diff_label)}</span></li>\n'
    index_html += '''        </ul>
    </section>
    <footer>
        LibOfManyCodes · 程式競賽題解
    </footer>
</body>
</html>
'''
    with open(out / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)

    return written


def git_commit_message_wrc() -> str:
    """commit subject：wrc_{YYYY}/{MM}/{DD}-{HH}.{MM}_done"""
    return datetime.now().strftime("wrc_%Y/%m/%d-%H.%M_done")


def git_commit_push_repo(
    repo: Path, subject: str, description: str = ""
) -> tuple[bool, str]:
    """
    在 repo 根目錄 git add -A；若有變更則 commit（subject 必填，description 可選為第二段）；
    再 git pull --rebase 整合遠端（避免 push 因「需先 fetch」被拒），最後 git push。
    回傳 (成功與否, 給使用者看的訊息)。
    """
    if not (repo / ".git").is_dir():
        return False, f"略過（非 git 儲存庫）: {repo}"

    try:
        r = subprocess.run(
            ["git", "add", "-A"],
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if r.returncode != 0:
            return False, f"git add 失敗 ({repo}): {r.stderr or r.stdout}"

        st = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if st.returncode != 0:
            return False, f"git status 失敗 ({repo}): {st.stderr}"

        if st.stdout.strip():
            commit_cmd = ["git", "commit", "-m", subject]
            if description.strip():
                commit_cmd.extend(["-m", description.strip()])
            cm = subprocess.run(
                commit_cmd,
                cwd=repo,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if cm.returncode != 0:
                return False, f"git commit 失敗 ({repo}): {cm.stderr or cm.stdout}"

        pr = subprocess.run(
            ["git", "pull", "--rebase"],
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if pr.returncode != 0:
            return False, (
                f"git pull --rebase 失敗 ({repo})，請手動解決衝突後再 push：\n"
                f"{pr.stderr or pr.stdout}"
            )

        pu = subprocess.run(
            ["git", "push"],
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if pu.returncode != 0:
            return False, f"git push 失敗 ({repo}): {pu.stderr or pu.stdout}"

        return True, f"已 push: {repo}"
    except FileNotFoundError:
        return False, "找不到 git 執行檔，請安裝 Git 並加入 PATH"
    except OSError as e:
        return False, f"git 執行錯誤: {e}"


def git_push_codelib_and_site(code_dir: str, output_dir: str) -> int:
    """
    依序對 CodeLib 與 chanaaaaaaa.github.io 根目錄 commit + push。
    code_dir 預設為 .../CodeLib/code；output_dir 預設為 .../chanaaaaaaa.github.io/coding。
    """
    code_root = Path(code_dir).resolve().parent
    site_root = Path(output_dir).resolve().parent
    roots: list[Path] = []
    for p in (code_root, site_root):
        rp = p.resolve()
        if rp not in roots:
            roots.append(rp)

    msg = git_commit_message_wrc()
    print("\n--- Git：commit & push ---")
    print(f"commit 訊息: {msg}")
    try:
        desc = input("description（直接 Enter 略過）: ")
    except EOFError:
        desc = ""
    desc = (desc or "").strip()

    exit_code = 0
    for root in roots:
        ok, info = git_commit_push_repo(root, msg, desc)
        print(info)
        if not ok and "略過" not in info:
            exit_code = 1
    return exit_code


def main():
    parser = argparse.ArgumentParser(description="建置 CodeLib 題解網站（輸出至 coding/）")
    parser.add_argument("--code-dir", default=DEFAULT_CODELIB, help="CodeLib/code 目錄路徑")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="輸出目錄（預設為 coding/）")
    parser.add_argument("--links", type=int, default=6, help="每頁顯示的其他題目連結數量")
    parser.add_argument("--seed", type=int, default=None, help="隨機種子")
    parser.add_argument(
        "--skip-git-push",
        action="store_true",
        help="不執行 CodeLib / chanaaaaaaa.github.io 的 git commit 與 push",
    )
    args = parser.parse_args()

    code_dir = args.code_dir if os.path.exists(args.code_dir) else ALT_CODELIB
    if not os.path.exists(code_dir):
        print(f"錯誤：找不到 CodeLib/code 目錄")
        print(f"請使用 --code-dir 指定路徑")
        return 1

    if args.seed is not None:
        random.seed(args.seed)

    output_dir = os.path.abspath(args.output)
    meta_path = Path(output_dir) / "meta.json"
    problems_path = Path(output_dir) / "data" / "problems.json"

    existing_meta = load_meta(meta_path)
    existing_problems = load_problems(problems_path)

    print(f"掃描目錄：{code_dir}")
    scanned = collect_problems(code_dir)
    print(f"找到 {len(scanned)} 個 .cpp 題目")

    if not scanned:
        print("沒有找到任何題目")
        return 1

    merged_problems, merged_meta, new_count = merge_with_existing(
        scanned, existing_problems, existing_meta
    )
    kept = len(merged_problems) - new_count
    print(f"比對結果：既有 {kept} 筆保留不變，新增 {new_count} 筆，共 {len(merged_problems)} 筆")

    # 寫入 meta.json（僅新增，不覆蓋既有 key）
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(merged_meta, f, ensure_ascii=False, indent=2)

    count = build_pages(scanned, merged_problems, output_dir, merged_meta, args.links)
    print(f"本次新建 {count} 個題目頁面（既有 .html 未覆寫）；已更新 index.html 與 data/problems.json")
    print(f"輸出目錄：{output_dir}")
    print(f"提示：可編輯 meta.json 補充各題的「題目內容(content)」與「時間複雜度」")

    if not args.skip_git_push:
        git_rc = git_push_codelib_and_site(code_dir, output_dir)
        if git_rc != 0:
            return git_rc
    return 0


if __name__ == "__main__":
    exit(main() or 0)
