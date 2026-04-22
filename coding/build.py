#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CodeLib GitHub Pages 建置腳本（入口）。
掃描 CodeLib/code 內所有題目，為每題產生解題頁面，並可選 git push。

題目檔名建議與 CodeLib 正規化規則一致：
UVa_{num}、CSES_{num}、AtCoder_abc{場次}_{題目}、ZeroJudge_{小寫字母}{數字}、
Luogu_{題號字串}（如 Luogu_P1234）、LibreOJ_{num}、CodeForces_{字串}（如 CodeForces_1805A 或
CodeForces_1805_A）；複合題以「-」連接多個片段。

實作模組見 site_builder/ 目錄。
"""
from __future__ import annotations

import argparse
import json
import os
import random
from pathlib import Path

from site_builder.config import ALT_CODELIB, DEFAULT_CODELIB, DEFAULT_OUTPUT
from site_builder.data_merge import load_meta, load_problems, merge_with_existing
from site_builder.day_folders import prompt_new_day_folder_if_calendar_advanced
from site_builder.git_ops import git_push_codelib_and_site
from site_builder.html_pages import build_pages
from site_builder.scan import collect_problems
from site_builder.workspace import prompt_delete_build_artifacts


def main() -> int:
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
    parser.add_argument(
        "--skip-clean-build-artifacts",
        action="store_true",
        help="不詢問是否刪除 code 目錄內的 .exe / .o",
    )
    parser.add_argument(
        "--skip-new-day-folder",
        action="store_true",
        help="不詢問是否依日曆日建立新的 day-* 空白資料夾",
    )
    args = parser.parse_args()

    code_dir = args.code_dir if os.path.exists(args.code_dir) else ALT_CODELIB
    if not os.path.exists(code_dir):
        print("錯誤：找不到 CodeLib/code 目錄")
        print("請使用 --code-dir 指定路徑")
        return 1

    if args.seed is not None:
        random.seed(args.seed)

    if not args.skip_clean_build_artifacts:
        prompt_delete_build_artifacts(code_dir)

    if not args.skip_new_day_folder:
        prompt_new_day_folder_if_calendar_advanced(code_dir)

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

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(merged_meta, f, ensure_ascii=False, indent=2)

    count = build_pages(scanned, merged_problems, output_dir, merged_meta, args.links)
    print(
        f"本次新建 {count} 個題目頁面（既有 .html 未覆寫）；已更新 index.html 與 data/problems.json"
    )
    print(f"輸出目錄：{output_dir}")
    print("提示：可編輯 meta.json 補充各題的「題目內容(content)」與「時間複雜度」")

    if not args.skip_git_push:
        git_rc = git_push_codelib_and_site(code_dir, output_dir)
        if git_rc != 0:
            return git_rc
    return 0


if __name__ == "__main__":
    exit(main() or 0)
