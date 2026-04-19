# -*- coding: utf-8 -*-
"""從 .cpp 註解擷取題解、複雜度。"""
import re


def extract_from_code(code: str, problem_id: str) -> tuple:
    """嘗試從程式碼註解中擷取題解與時間複雜度"""
    solution = ""
    complexity = ""

    for pattern in [
        r"//\s*題解\s*[：:]\s*(.+?)(?:\n|$)",
        r"/\*\s*題解\s*[：:]\s*(.+?)\s*\*/",
        r"//\s*解法\s*[：:]\s*(.+?)(?:\n|$)",
    ]:
        m = re.search(pattern, code, re.DOTALL)
        if m:
            solution = m.group(1).strip()
            break

    for pattern in [
        r"//\s*時間複雜度\s*[：:]\s*(.+?)(?:\n|$)",
        r"/\*\s*時間複雜度\s*[：:]\s*(.+?)\s*\*/",
        r"//\s*複雜度\s*[：:]\s*(.+?)(?:\n|$)",
        r"//\s*Time\s*[Cc]omplexity\s*[：:]\s*(.+?)(?:\n|$)",
        r"//\s*O\s*\(\s*[^)]+\s*\)",
    ]:
        m = re.search(pattern, code, re.DOTALL)
        if m:
            complexity = m.group(1).strip() if m.lastindex else m.group(0).strip()
            break

    return solution or "（請自行補充）", complexity or "（請自行補充）"
