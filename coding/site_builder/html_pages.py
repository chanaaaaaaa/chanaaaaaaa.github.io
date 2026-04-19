# -*- coding: utf-8 -*-
"""產生題解 HTML、index、problems.json。"""
from __future__ import annotations

import html
import json
import random
from pathlib import Path

from .cpp_highlight import highlight_cpp, strip_pragma_lines
from .data_merge import safe_id_from_url
from .problem_meta import cpp_path_outer_folder_name, cpp_stem_to_share_label, format_problem_source

PAGE_TEMPLATE = """<!DOCTYPE html>
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
"""


def format_text_for_display(text: str) -> str:
    if not text or not text.strip():
        return ""
    return html.escape(text).replace("\n", "<br>")


def build_pages(
    scanned_problems: list,
    merged_problems: list,
    output_dir: str,
    meta: dict,
    num_links: int = 6,
) -> int:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "problems").mkdir(exist_ok=True)
    (out / "data").mkdir(exist_ok=True)

    written = 0
    share_snapshots: list[tuple[str, str]] = []

    for i, p in enumerate(scanned_problems):
        html_path = out / "problems" / f"{p['safe_id']}.html"
        if html_path.is_file():
            continue

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
            problem_link_html = (
                f'<p><a href="{p["link"]}" target="_blank" rel="noopener">'
                f"題目連結（原題／評測）</a></p>"
            )

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
        for day_folder, label in share_snapshots:
            print()
            print(f"每日亂捲直到跟皮卡丘一樣⚡️ {day_folder}")
            print("-")
            print("（待補）")
            print("-")
            print(f"->{label} - （題名待補）")
            print("（待補）")
            print("-")
            print("https://chanaaaaaaa.github.io/coding/index.html")
            print("https://github.com/chanaaaaaaa/CodeLib")
            print()

    TYPE_ORDER = [
        "圖論", "DP", "貪心", "排序", "搜尋", "數學", "字串", "資料結構", "模擬", "其他",
    ]
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

    index_html = """<!DOCTYPE html>
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
"""
    current_type = None
    for pl in problem_list:
        if pl["type"] != current_type:
            if current_type is not None:
                index_html += "        </ul>\n    </section>\n"
            current_type = pl["type"]
            index_html += "    <section class=\"problem-section\">\n"
            index_html += f'        <h2 class="section-title">{html.escape(current_type)}</h2>\n'
            index_html += '        <ul class="problem-list">\n'
        diff_label = DIFFICULTY_ORDER.get(pl["difficulty"], str(pl["difficulty"]))
        source_str = format_problem_source(pl["id"])
        index_html += (
            f'            <li><a href="{pl["url"]}" class="problem-title">{html.escape(pl["title"])}</a>'
            f'<span class="problem-source">{html.escape(source_str)}</span>'
            f'<span class="difficulty-badge">{html.escape(diff_label)}</span></li>\n'
        )
    index_html += """        </ul>
    </section>
    <footer>
        LibOfManyCodes · 程式競賽題解
    </footer>
</body>
</html>
"""
    with open(out / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)

    return written
