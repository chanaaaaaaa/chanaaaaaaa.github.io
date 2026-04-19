# -*- coding: utf-8 -*-
"""meta.json、problems.json 讀寫與合併。"""
import json
from pathlib import Path


def load_meta(meta_path: Path) -> dict:
    if not meta_path.exists():
        return {}
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def load_problems(problems_path: Path) -> list:
    if not problems_path.exists():
        return []
    try:
        with open(problems_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("problems", [])
    except Exception:
        return []


def safe_id_from_url(url: str) -> str:
    if "/" in url:
        url = url.split("/")[-1]
    return url.replace(".html", "") if url.endswith(".html") else url


def merge_with_existing(
    scanned_problems: list,
    existing_problems: list,
    existing_meta: dict,
) -> tuple:
    """
    比對掃描結果與現有 problems.json、meta.json。
    - 已出現（id + safe_id 在 problems.json 中）：保留現有資訊，不編輯
    - 未曾出現：新增至 problems（僅 id/title/url）與 meta（預填欄位）
    回傳 (merged_problems, merged_meta, new_count)
    """
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
            merged_problems.append(existing_by_key[key])
        else:
            new_entry = {
                "id": p["id"],
                "title": p["title"],
                "url": f"problems/{p['safe_id']}.html",
            }
            merged_problems.append(new_entry)
            new_count += 1

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

    scanned_keys = {(p["id"], p["safe_id"]) for p in scanned_problems}
    for p in existing_problems:
        sid = safe_id_from_url(p.get("url", ""))
        if (p.get("id", ""), sid) not in scanned_keys:
            merged_problems.append(p)

    return merged_problems, merged_meta, new_count
