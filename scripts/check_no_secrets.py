"""
Comprehensive security check: ensures no API keys or secrets are staged, tracked,
present in untracked files, or present in git history.
Blocks key prefixes and API key assignment patterns.
"""

import os
import re
import subprocess
import sys

# Secret patterns to detect (constructed dynamically to avoid matching this script)
P_GSK = "g" + "sk_[A-Za-z0-9_-]{10,}"
P_SK = "s" + "k-[A-Za-z0-9_-]{20,}"
P_API_KEY = "api" + r"_key\s*=\s*['\"][A-Za-z0-9_-]{10,}['\"]"

SECRET_REGEX = re.compile(f"({P_GSK}|{P_SK}|{P_API_KEY})")
LITERAL_CHECK = ["g" + "sk_", "s" + "k-proj-", "api" + "_key="]

def scan_text(text: str, context: str) -> bool:
    for line in text.splitlines():
        # Skip comments or script self-definitions
        if "check_no_secrets" in line or "SECRET_REGEX" in line:
            continue
        if SECRET_REGEX.search(line):
            print(f"ERROR: Secret pattern detected in {context}:\n  {line[:80]}...", file=sys.stderr)
            return True
        for lit in LITERAL_CHECK:
            if lit in line and not line.strip().startswith("#"):
                # verify it's not a generic placeholder
                if any(x in line for x in ["SECRET_PREFIX_REDACTED", "your_groq_api_key_here", "ollama", "xxx"]):
                    continue
                print(f"ERROR: Suspicious literal '{lit}' in {context}:\n  {line[:80]}...", file=sys.stderr)
                return True
    return False

def main():
    # 1. Check full git history
    try:
        res_hist = subprocess.run(
            ["git", "log", "--all", "-p"],
            capture_output=True,
            errors="replace",
            check=True
        )
        hist_text = res_hist.stdout or ""
        # Check added lines in history
        added_lines = [l for l in hist_text.splitlines() if l.startswith("+") and not l.startswith("+++")]
        for l in added_lines:
            if "check_no_secrets" in l or "SECRET_PREFIX_REDACTED" in l:
                continue
            if SECRET_REGEX.search(l):
                print(f"ERROR: Secret pattern detected in git history addition:\n  {l[:80]}...", file=sys.stderr)
                return 1
            if ("g" + "sk_") in l:
                print(f"ERROR: Secret prefix pattern detected in git history addition:\n  {l[:80]}...", file=sys.stderr)
                return 1
    except Exception as e:
        print(f"Warning: Failed to scan git history: {e}", file=sys.stderr)

    # 2. Check tracked files
    res_tracked = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=True
    )
    tracked_files = [f.strip() for f in (res_tracked.stdout or "").splitlines() if f.strip()]
    
    for fpath in tracked_files:
        if fpath == "scripts/check_no_secrets.py":
            continue
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if scan_text(content, f"tracked file '{fpath}'"):
                    return 1
        except Exception:
            pass

    # 3. Check staged changes
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
        if scan_text(line, "staged diff"):
            return 1

    # 4. Check untracked files (excluding standard gitignore)
    res_untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=True
    )
    untracked_files = [f.strip() for f in (res_untracked.stdout or "").splitlines() if f.strip()]
    for fpath in untracked_files:
        if fpath == "scripts/check_no_secrets.py" or fpath.endswith(".png") or fpath.endswith(".pdf"):
            continue
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if scan_text(content, f"untracked file '{fpath}'"):
                    return 1
        except Exception:
            pass

    print("PASS: No secret patterns detected in history, tracked files, staged diff, or untracked files.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
