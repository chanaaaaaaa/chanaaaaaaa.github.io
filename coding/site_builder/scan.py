# -*- coding: utf-8 -*-
"""掃描 CodeLib/code 內所有 .cpp。"""
import re
from pathlib import Path

from .extract import extract_from_code
from .problem_meta import find_problem_link


def collect_problems(code_dir: str) -> list:
    """掃描 code 目錄內所有 .cpp 檔，每個檔案以檔名（不含 .cpp）作為題目 ID 建立一題"""
    code_path = Path(code_dir)
    if not code_path.exists():
        return []

    problems = []
    seen_safe_ids = {}

    for cpp_file in sorted(code_path.rglob("*.cpp")):
        if cpp_file.name.endswith(".o") or "obj" in str(cpp_file).lower():
            continue

        problem_id = cpp_file.stem

        try:
            with open(cpp_file, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()
        except Exception:
            code = "// 無法讀取程式碼"

        base_safe = re.sub(r"[^\w\s-]", "", problem_id).strip().replace(" ", "-")
        if not base_safe:
            base_safe = "p"
        base_safe = base_safe[:50]

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
