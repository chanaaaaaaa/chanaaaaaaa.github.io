# -*- coding: utf-8 -*-
"""Git commit / pull --rebase / push。"""
from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path


def git_commit_message_wrc() -> str:
    return datetime.now().strftime("wrc_%Y/%m/%d-%H.%M_done")


def git_commit_push_repo(
    repo: Path, subject: str, description: str = ""
) -> tuple[bool, str]:
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
