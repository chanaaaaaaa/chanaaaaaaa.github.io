#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析 CodeLib 程式碼的時間複雜度，並更新 meta.json
"""

import os
import re
import json
from pathlib import Path

CODE_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "git", "CodeLib", "code")
ALT_CODE_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "CodeLib", "code")


def collect_problems(code_dir: str) -> list:
    """與 build.py 相同的邏輯：收集題目與程式碼"""
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
            code = ""

        problems.append({"id": folder_name, "code": code})
        seen.add(folder_name)

    return problems


def analyze_complexity(code: str) -> str:
    """
    根據程式碼結構推斷時間複雜度
    使用啟發式規則，非 100% 準確
    """
    code = re.sub(r'//.*', '', code)  # 移除單行註解
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)  # 移除多行註解
    lines = code.split('\n')

    # 先檢查是否有註解中的複雜度
    full_code = '\n'.join(lines)
    for pat in [
        r'時間複雜度\s*[：:]\s*O\s*\(([^)]+)\)',
        r'複雜度\s*[：:]\s*O\s*\(([^)]+)\)',
        r'Time\s*[Cc]omplexity\s*[：:]\s*O\s*\(([^)]+)\)',
        r'//\s*O\s*\(\s*([^)]+)\s*\)',
    ]:
        m = re.search(pat, full_code)
        if m:
            return f"O({m.group(1).strip()})"

    # 統計迴圈與演算法特徵
    has_bfs = bool(re.search(r'\b(bfs|BFS|queue\s*<|queue\.)', code))
    has_dfs = bool(re.search(r'\b(dfs|DFS|stack\s*<|stack\.|recursion|遞迴)', code))
    has_dijkstra = bool(re.search(r'\b(dijkstra|priority_queue|pq\.)', code))
    has_binary_search = bool(re.search(r'\b(binary_search|lower_bound|upper_bound|bisect)', code))
    has_sort = bool(re.search(r'\bsort\s*\(', code))
    has_map = bool(re.search(r'\b(map\s*<|unordered_map)', code))
    has_set = bool(re.search(r'\b(set\s*<|unordered_set)', code))
    has_floyd = bool(re.search(r'\b(floyd|Floyd|k\s*<\s*n|warshall)', code))

    # 迴圈深度
    max_nested = 0
    indent_stack = [0]
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        # 簡化：計算 for/while 出現次數
        pass

    for_count = len(re.findall(r'\bfor\s*\(', code))
    while_count = len(re.findall(r'\bwhile\s*\(', code))
    loop_total = for_count + while_count

    # 演算法特徵優先
    if has_floyd:
        return "O(V³)"
    if has_dijkstra:
        return "O((V + E) log V)"
    if has_bfs or has_dfs:
        return "O(V + E)"
    if has_binary_search and loop_total <= 1:
        return "O(log n)" if loop_total == 0 else "O(n log n)"
    if has_sort and loop_total <= 2:
        return "O(n log n)"
    # 迴圈數量推斷（保守：多數競賽題 2–3 個迴圈為 O(n²)）
    if loop_total >= 6:
        return "O(n³)"
    if loop_total >= 2:
        return "O(n²)"
    if loop_total >= 1:
        return "O(n)"
    if has_map or has_set:
        return "O(n log n)"  # 或 O(n) for unordered
    # 簡單 I/O
    return "O(1)"


def infer_type(code: str, problem_id: str) -> str:
    """根據程式碼與題目 ID 推斷題目類型"""
    code_lower = code.lower()
    pid = problem_id.lower()

    # 圖論
    if re.search(r'\b(bfs|dfs|queue\s*<|adjacency|graph|floyd|dijkstra|priority_queue)', code_lower):
        return "圖論"
    # DP
    if re.search(r'\b(dp\[|memo|recurrence|遞迴)', code_lower) or 'dp' in code_lower:
        return "DP"
    # 數學
    if re.search(r'\b(gcd|lcm|prime|mod\s*|pow\(|factorial)', code_lower):
        return "數學"
    # 字串
    if re.search(r'\b(string|substr|regex|getline|cin\s*>>\s*\w+;)', code_lower):
        return "字串"
    # 排序 + 貪心
    if re.search(r'\bsort\s*\(', code_lower):
        if re.search(r'\b(greedy|貪心|two.?pointer|雙指標)', code_lower):
            return "貪心"
        return "排序"
    # 搜尋
    if re.search(r'\b(binary_search|lower_bound|upper_bound|bisect)', code_lower):
        return "搜尋"
    # 資料結構
    if re.search(r'\b(segment_tree|BIT|fenwick|map\s*<|set\s*<|unordered_map|unordered_set)', code_lower):
        return "資料結構"
    # 模擬（簡單迴圈為主）
    if re.search(r'\b(for|while)\s*\(', code_lower) and not re.search(r'\b(sort|queue|stack|map|set)\s*', code_lower):
        return "模擬"
    return "其他"


def infer_difficulty(complexity: str, ptype: str, problem_id: str) -> int:
    """
    推斷難度 1–5（1=入門, 2=簡單, 3=中等, 4=困難, 5=進階）
    """
    pid = problem_id.lower()
    # 入門題：a001, a003 等 ZeroJudge 基礎
    if re.match(r'^a00[1-5]$', pid.replace(' ', '')):
        return 1
    if 'O(1)' in complexity:
        return 1
    if 'O(n)' in complexity and 'log' not in complexity:
        return 2
    if 'O(n log n)' in complexity or 'O(log n)' in complexity:
        return 2
    if 'O(n²)' in complexity or 'O(n2)' in complexity:
        return 3
    if 'O(V + E)' in complexity:
        return 3
    if 'O(n³)' in complexity or 'O(n3)' in complexity or 'O(V³)' in complexity:
        return 4
    if 'O((V + E) log V)' in complexity:
        return 4
    return 3


def main():
    code_dir = CODE_DIR if os.path.exists(CODE_DIR) else ALT_CODE_DIR
    if not os.path.exists(code_dir):
        print("找不到 CodeLib/code 目錄")
        return 1

    script_dir = Path(__file__).parent
    meta_path = script_dir / "meta.json"

    # 載入現有 meta
    meta = {}
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in data.items():
            if not k.startswith("_"):
                meta[k] = v

    problems = collect_problems(code_dir)
    print(f"分析 {len(problems)} 個題目...")

    for p in problems:
        complexity = analyze_complexity(p["code"])
        ptype = infer_type(p["code"], p["id"])
        difficulty = infer_difficulty(complexity, ptype, p["id"])
        pid = p["id"]
        if pid not in meta:
            meta[pid] = {}
        if not isinstance(meta[pid], dict):
            meta[pid] = {}
        meta[pid]["complexity"] = complexity
        if "type" not in meta[pid]:
            meta[pid]["type"] = ptype
        if "difficulty" not in meta[pid]:
            meta[pid]["difficulty"] = difficulty

    # 保留 _說明 與 _範例
    output = {
        "_說明": "在此補充各題的題解、時間複雜度、類型(type)、難度(difficulty 1-5)。",
        "_範例": {},
    }
    for k, v in sorted(meta.items()):
        output[k] = v

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"已更新 meta.json")
    return 0


if __name__ == "__main__":
    exit(main() or 0)
