#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CodeLib GitHub Pages 建置腳本
掃描 CodeLib/code 內所有題目，為每題產生解題頁面（含題解、時間複雜度），並在每頁附上隨機的其他題目連結。
輸出至 chanaaaaaaa.github.io/coding
"""

import os
import re
import json
import random
import html
import argparse
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
      MathJax = {
        tex: {
          inlineMath: [['\\(', '\\)']],
          displayMath: [['\\[', '\\]']]
        }
      };
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


def format_problem_source(problem_id: str) -> str:
    """將題目 ID 轉為「網站與編號」顯示字串"""
    pid = problem_id.strip()
    parts = []
    # ZeroJudge 格式：a001, b059, c123
    zj_match = re.findall(r'\b([a-z]\d+)\b', pid, re.I)
    for m in zj_match:
        parts.append(f"ZeroJudge {m.upper()}")
    # UVa 格式：uva924, uva 10931
    uva_match = re.findall(r'uva\s*(\d+)', pid, re.I)
    for m in uva_match:
        parts.append(f"UVa {m}")
    # CSES
    if re.search(r'cses', pid, re.I):
        num = re.search(r'\d+', pid)
        if num:
            parts.append(f"CSES {num.group(0)}")
    # APCS
    if re.search(r'apcs', pid, re.I):
        year = re.search(r'20\d{2}', pid)
        parts.append(f"APCS {year.group(0) if year else ''}".strip())
    # AtCoder
    if re.search(r'atcoder|atcode', pid, re.I):
        parts.append("AtCoder")
    # day-xxx
    if re.match(r'day-\d+', pid, re.I):
        parts.append(pid)
    if not parts:
        return pid
    return " · ".join(parts)


def find_problem_link(problem_id: str) -> str:
    """根據題目 ID 推測 VJudge / ZeroJudge 連結"""
    problem_id = problem_id.strip().lower()
    uva_match = re.search(r'uva\s*(\d+)', problem_id) or re.search(r'(\d{4,5})', problem_id)
    if uva_match:
        return f'https://vjudge.net/problem/UVA-{uva_match.group(1)}'
    zj_match = re.search(r'([a-z])\s*(\d+)', problem_id) or re.search(r'([a-z]\d+)', problem_id)
    if zj_match:
        pid = zj_match.group(0).replace(' ', '').upper()
        return f'https://zerojudge.tw/ShowProblem?problemid={pid}'
    if 'cses' in problem_id:
        num = re.search(r'\d+', problem_id)
        if num:
            return f'https://cses.fi/problemset/task/{num.group(0)}'
    return ''


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


def collect_problems(code_dir: str) -> list:
    """掃描 code 目錄，收集所有題目"""
    code_path = Path(code_dir)
    if not code_path.exists():
        return []

    problems = []
    seen = set()

    for cpp_file in code_path.rglob("*.cpp"):
        if cpp_file.name.endswith('.o') or 'obj' in str(cpp_file).lower():
            continue
        rel = cpp_file.relative_to(code_path)
        parts = rel.parts
        folder_name = parts[-2] if len(parts) >= 2 else (parts[0] if parts else str(rel.parent))

        if folder_name in seen:
            continue

        folder = cpp_file.parent
        preferred = folder / "c.cpp"
        if preferred.exists():
            cpp_file = preferred
        else:
            cpp_files = list(folder.glob("*.cpp"))
            if cpp_files:
                cpp_file = sorted(cpp_files)[0]

        try:
            with open(cpp_file, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()
        except Exception:
            code = "// 無法讀取程式碼"

        safe_id = re.sub(r'[^\w\s-]', '', folder_name).strip().replace(' ', '-')
        if not safe_id:
            safe_id = f"p{len(problems)}"
        safe_id = safe_id[:50]

        solution, complexity = extract_from_code(code, folder_name)

        problems.append({
            "id": folder_name,
            "safe_id": safe_id,
            "title": folder_name,
            "code": code,
            "link": find_problem_link(folder_name),
            "solution": solution,
            "complexity": complexity,
        })
        seen.add(folder_name)

    return problems


def build_pages(problems: list, output_dir: str, meta: dict, num_links: int = 6):
    """產生各題目頁面與 index"""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "problems").mkdir(exist_ok=True)
    (out / "data").mkdir(exist_ok=True)

    problem_list = []
    for i, p in enumerate(problems):
        url = f"problems/{p['safe_id']}.html"
        problem_list.append({"id": p["id"], "title": p["title"], "url": url})

        # 優先使用 meta.json 的內容
        m = meta.get(p["id"], {}) or meta.get(p["safe_id"], {})
        summary = m.get("summary") or m.get("description") or ""
        solution = m.get("solution") or p["solution"]
        complexity = m.get("complexity") or p["complexity"]

        others = [x for j, x in enumerate(problems) if j != i]
        random.shuffle(others)
        links = others[:num_links]

        other_links_html = " ".join(
            f'<a href="{x["safe_id"]}.html" class="problem-link">{html.escape(x["title"])}</a>'
            for x in links
        )

        problem_link_html = ""
        if p["link"]:
            problem_link_html = f'<p><a href="{p["link"]}" target="_blank" rel="noopener">題目連結（VJudge / ZeroJudge）</a></p>'

        summary_html = format_text_for_display(summary) or "（請自行查閱題目描述）"
        solution_html = format_text_for_display(solution) or "（請自行補充）"
        complexity_html = html.escape(complexity)

        code_html = highlight_cpp(p["code"])
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

        with open(out / "problems" / f"{p['safe_id']}.html", "w", encoding="utf-8") as f:
            f.write(html_content)

    # 依類型與難度分組排序
    TYPE_ORDER = ["圖論", "DP", "貪心", "排序", "搜尋", "數學", "字串", "資料結構", "模擬", "其他"]
    DIFFICULTY_ORDER = {1: "入門", 2: "簡單", 3: "中等", 4: "困難", 5: "進階"}

    def get_type(p):
        t = meta.get(p["id"], {}).get("type") or meta.get(p["safe_id"], {}).get("type") or "其他"
        return t

    def get_difficulty(p):
        d = meta.get(p["id"], {}).get("difficulty") or meta.get(p["safe_id"], {}).get("difficulty") or 3
        return int(d) if isinstance(d, (int, float)) else 3

    grouped = {}
    for p in problems:
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
                    "url": f"problems/{p['safe_id']}.html",
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
                    "url": f"problems/{p['safe_id']}.html",
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

    return len(problems)


def main():
    parser = argparse.ArgumentParser(description="建置 CodeLib 題解網站（輸出至 coding/）")
    parser.add_argument("--code-dir", default=DEFAULT_CODELIB, help="CodeLib/code 目錄路徑")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="輸出目錄（預設為 coding/）")
    parser.add_argument("--links", type=int, default=6, help="每頁顯示的其他題目連結數量")
    parser.add_argument("--seed", type=int, default=None, help="隨機種子")
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
    meta = load_meta(meta_path)

    print(f"掃描目錄：{code_dir}")
    problems = collect_problems(code_dir)
    print(f"找到 {len(problems)} 個題目")

    if not problems:
        print("沒有找到任何題目")
        return 1

    count = build_pages(problems, output_dir, meta, args.links)
    print(f"已產生 {count} 個題目頁面與 index.html")
    print(f"輸出目錄：{output_dir}")
    print(f"提示：可編輯 meta.json 補充各題的「題目大意(summary)」、「題解(solution)」與「時間複雜度」")
    return 0


if __name__ == "__main__":
    exit(main() or 0)
