#!/usr/bin/env python3
"""
Pre-commit security check: ensure no API keys or secrets are staged or tracked in git.
"""

import re
import subprocess
import sys

SECRET_REGEX = re.compile(r"g" + r"sk_[A-Za-z0-9_-]{20,}")

def main():
    # 1. Check tracked files
    res = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=True
    )
    tracked_files = [f.strip() for f in (res.stdout or "").splitlines() if f.strip()]
    
    for fpath in tracked_files:
        if fpath == "scripts/check_no_secrets.py":
            continue
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if SECRET_REGEX.search(content):
                    print(f"ERROR: Potential secret detected in tracked file: {fpath}", file=sys.stderr)
                    return 1
        except Exception:
            pass

    # 2. Check staged changes
    res_staged = subprocess.run(
        ["git", "diff", "--cached"],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=True
    )
    staged_diff = res_staged.stdout or ""
    lines = [line for line in staged_diff.splitlines() if line.startswith("+") and not line.startswith("+++")]
    for line in lines:
        if SECRET_REGEX.search(line):
            print("ERROR: Potential secret detected in staged addition:", file=sys.stderr)
            return 1

    print("PASS: No secret patterns detected in git.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
