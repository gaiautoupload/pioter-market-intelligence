"""Commit generated public files and push to an already configured GitHub remote."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REMOTE = "https://github.com/gaiautoupload/pioter-market-intelligence.git"
GIT = os.getenv("GIT_EXE") or shutil.which("git") or r"C:\Program Files\Git\cmd\git.exe"


def run(*args: str, check=True) -> str:
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check)
    return result.stdout.strip()


def git(*args: str, check=True) -> str:
    return run(GIT, "-c", f"safe.directory={ROOT}", *args, check=check)


def main():
    remote = git("remote", "get-url", "github", check=False)
    if not remote:
        git("remote", "add", "github", os.getenv("GITHUB_REMOTE_URL", DEFAULT_REMOTE))
        remote = git("remote", "get-url", "github")
    if "github.com" not in remote.lower():
        raise SystemExit("GitHub remote 不是 github.com；停止自動發布。")
    git("add", "dist/data/latest.json", "dist/data/analysis.json", "dist/data/brief.md", "dist/data/market.json")
    changed = subprocess.run([GIT, "-c", f"safe.directory={ROOT}", "diff", "--cached", "--quiet"], cwd=ROOT).returncode != 0
    if changed:
        git("-c", "user.name=Pioter Scheduler", "-c", "user.email=pioter@local.invalid", "commit", "-m", "data: daily refresh " + datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %z"))
    git("push", "github", "HEAD:main")
    print(json.dumps({"remote": "github", "changed": changed, "status": "pushed"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
