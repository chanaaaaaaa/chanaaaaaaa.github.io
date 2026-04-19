# -*- coding: utf-8 -*-
"""
在 CodeLib/code 下維護 day-{n} 資料夾：
若「今日」與「編號最大之 day-* 資料夾」的最後修改日期（日曆日）不同，
則可經詢問後建立新的空白資料夾 day-{max+1}。
若尚無任何 day-*，則可經詢問後建立 day-1。
"""
from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path


def _pending_new_day_folder(code_dir: str) -> tuple[Path, str] | None:
    """
    若符合「應新建」條件且目標路徑尚不存在，回傳 (將建立的路徑, 說明)；否則 None。
    已存在或無需新建時會印出簡短訊息並回傳 None。
    """
    root = Path(code_dir)
    if not root.is_dir():
        return None

    day_dirs: list[tuple[int, Path]] = []
    for p in root.iterdir():
        if not p.is_dir():
            continue
        m = re.match(r"^day-(\d+)$", p.name, re.I)
        if m:
            day_dirs.append((int(m.group(1)), p))

    if not day_dirs:
        new_path = root / "day-1"
        if new_path.exists():
            return None
        msg = "尚無任何 day-* 資料夾，將建立空白資料夾 day-1。"
        return new_path, msg

    max_n, latest_path = max(day_dirs, key=lambda x: x[0])
    latest_mtime = datetime.fromtimestamp(latest_path.stat().st_mtime)
    latest_day = latest_mtime.date()
    today = date.today()

    if today == latest_day:
        return None

    new_name = f"day-{max_n + 1}"
    new_path = root / new_name
    if new_path.exists():
        print(f"預期新建 {new_path.name} 已存在，略過。")
        return None

    msg = (
        f"今日（{today}）與最新 day 資料夾「{latest_path.name}」"
        f"最後修改日（{latest_day}）不同，將建立空白資料夾 {new_name}。"
    )
    return new_path, msg


def prompt_new_day_folder_if_calendar_advanced(code_dir: str) -> Path | None:
    """
    若符合日曆條件需新建 day-*，於 console 詢問；輸入 y/yes 才建立。
    回傳：若新建了資料夾則為該 Path；否則 None。
    """
    pending = _pending_new_day_folder(code_dir)
    if pending is None:
        return None

    new_path, explanation = pending
    print(explanation)
    try:
        ans = input("是否建立此空白資料夾？[y/N]: ").strip().lower()
    except EOFError:
        ans = ""

    if ans not in ("y", "yes"):
        print("已略過，未建立。")
        return None

    new_path.mkdir(parents=True, exist_ok=True)
    print(f"已建立：{new_path.resolve()}")
    return new_path
