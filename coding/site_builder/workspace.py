# -*- coding: utf-8 -*-
"""掃描並可選刪除編譯產物 .exe / .obj。"""
from pathlib import Path


def find_build_artifacts(root: Path) -> tuple[list[Path], list[Path]]:
    """遞迴列出 .exe 與 .o（副檔名不分大小寫）。"""
    exes: list[Path] = []
    objs: list[Path] = []
    if not root.is_dir():
        return exes, objs
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        suf = p.suffix.lower()
        if suf == ".exe":
            exes.append(p)
        elif suf == ".o":
            objs.append(p)
    return exes, objs


def prompt_delete_build_artifacts(code_dir: str) -> None:
    """
    若在 code_dir 下發現 .exe 或 .o，於 console 詢問是否刪除。
    輸入 y/yes 才刪除；直接 Enter 或其他輸入則略過。
    """
    root = Path(code_dir)
    exes, objs = find_build_artifacts(root)
    if not exes and not objs:
        return

    print(
        f"掃描到 {len(exes)} 個 .exe 與 {len(objs)} 個 .o 檔（於 {root.resolve()}）"
    )
    try:
        ans = input("是否刪除這些檔案？[y/N]: ").strip().lower()
    except EOFError:
        ans = ""

    if ans not in ("y", "yes"):
        print("已略過，未刪除。")
        return

    n = 0
    for p in exes + objs:
        try:
            p.unlink()
            n += 1
        except OSError as e:
            print(f"無法刪除 {p}: {e}")
    print(f"已刪除 {n} 個檔案。")
