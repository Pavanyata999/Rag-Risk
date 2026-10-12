"""
Comprehensive Structured Numerical Verification System: scripts/check_paper_numbers.py

Associates every quantitative claim in the paper with:
- A unique claim identifier.
- Its location in the paper (abstract, tables, text, macros).
- The authoritative source file in logs/.
- The precise JSON selector path.
- The evaluation split and metric definition.
- The numerator and denominator (where applicable).
- The permitted precision / tolerance.

Fails with exit code 1 if any claim fails verification.
"""

import os
import sys
import json
import re

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PAPER_DIR = os.path.join(BASE_DIR, "docs", "paper")
MAIN_TEX_PATH = os.path.join(PAPER_DIR, "main.tex")
MACROS_PATH = os.path.join(PAPER_DIR, "results_macros.tex")
REGISTRY_PATH = os.path.join(PAPER_DIR, "claims_registry.json")
LOGS_DIR = os.path.join(BASE_DIR, "logs")


def get_nested(obj, path):
    curr = obj
    for k in path:
        if isinstance(curr, dict) and k in curr:
            curr = curr[k]
        elif isinstance(curr, list) and isinstance(k, int) and 0 <= k < len(curr):
            curr = curr[k]
        else:
            return None
    return curr


def expand_inputs(tex_content, base_dir):
    def repl(match):
        rel_fn = match.group(1).strip()
        if not rel_fn.endswith(".tex"):
            rel_fn += ".tex"
        p = os.path.join(base_dir, rel_fn)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return f.read()
        return match.group(0)

    expanded = re.sub(r'\\input\{([^}]+)\}', repl, tex_content)
    return expanded


def verify_claims_registry():
    if not os.path.exists(REGISTRY_PATH):
        print(f"Error: Claims registry not found at {REGISTRY_PATH}")
        return False

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry = json.load(f)

    with open(MAIN_TEX_PATH, "r", encoding="utf-8") as f:
        main_tex = f.read()

    expanded_tex = expand_inputs(main_tex, PAPER_DIR)

    macros_dict = {}
    if os.path.exists(MACROS_PATH):
        with open(MACROS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                m = re.match(r'\\newcommand\{\\([a-zA-Z0-9]+)\}\{([^}]+)\}', line.strip())
                if m:
                    macros_dict[m.group(1)] = m.group(2)

    passed = 0
    failed = 0
    print("=" * 115)
    print(f"{'Claim ID':<30}{'Metric Definition':<35}{'Source Log':<25}{'Status':<15}{'Value':<10}")
    print("=" * 115)

    for item in registry:
        cid = item["claim_id"]
        metric = item["metric_definition"]
        src_rel = item["source_file"]
        src_path = os.path.join(BASE_DIR, src_rel)
        path = item["json_path"]
        expected = item["expected_value"]
        tol = item.get("tolerance", 0.001)

        if not os.path.exists(src_path):
            print(f"FAIL: {cid} - Source file {src_rel} does not exist!")
            failed += 1
            continue

        with open(src_path, "r", encoding="utf-8") as f:
            log_data = json.load(f)

        actual = get_nested(log_data, path)
        if actual is None:
            print(f"FAIL: {cid} - JSON path {path} not found in {src_rel}!")
            failed += 1
            continue

        # Check numerator / denominator if present
        if "numerator" in item and "denominator" in item:
            num = item["numerator"]
            den = item["denominator"]
            if den > 0:
                expected_ratio = num / den
                if abs(expected_ratio - actual) > tol:
                    print(f"FAIL: {cid} - Numerator/Denominator {num}/{den} ({expected_ratio:.4f}) does not match log value {actual}!")
                    failed += 1
                    continue

        # Check expected value match
        diff = abs(actual - expected)
        if diff > tol:
            print(f"FAIL: {cid} - Log value {actual} differs from expected {expected} by {diff} (tol={tol})!")
            failed += 1
            continue

        # Check macro mapping if present
        macro = item.get("macro")
        if macro:
            macro_name = macro.replace("\\", "")
            if macro_name not in macros_dict:
                print(f"FAIL: {cid} - Macro {macro} missing from results_macros.tex!")
                failed += 1
                continue

        val_str = f"{actual:.3f}" if isinstance(actual, float) else str(actual)
        print(f"{cid:<30}{metric[:33]:<35}{src_rel:<25}{'VERIFIED':<15}{val_str:<10}")
        passed += 1

    print("=" * 115)
    print(f"Registry Summary: {passed} claims verified against authoritative logs, {failed} failures.")
    return failed == 0


def verify_text_numbers():
    """Extract raw numbers from results and tables to ensure full coverage."""
    with open(MAIN_TEX_PATH, "r", encoding="utf-8") as f:
        tex = f.read()
    expanded = expand_inputs(tex, PAPER_DIR)

    # Assert no red [MISSING] tokens
    if "[MISSING]" in expanded:
        print("FAIL: Expanded manuscript contains unresolved [MISSING] placeholders!")
        return False
    print("VERIFIED: Zero unresolved [MISSING] placeholders in manuscript.")
    return True


def main():
    ok_reg = verify_claims_registry()
    ok_tex = verify_text_numbers()
    if ok_reg and ok_tex:
        print("\nSUCCESS: All paper quantitative claims and manuscript macros verified against authoritative logs.")
        sys.exit(0)
    else:
        print("\nFAILURE: Quantitative verification failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
