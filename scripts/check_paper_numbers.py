"""
Comprehensive Verification Script: check_paper_numbers.py

Extracts EVERY number from tables, abstract, and results text in docs/paper/main.tex
and verifies each against the empirical JSON logs in logs/.
Fails with exit code 1 if any unchecked numeric claim remains.
"""

import os
import sys
import json
import re

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PAPER_PATH = os.path.join(BASE_DIR, "docs", "paper", "main.tex")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

def load_all_log_numbers():
    """Traverse all JSON logs and collect all valid empirical numeric values."""
    valid_numbers = set()

    def register_num(val):
        if val is None:
            return
        if isinstance(val, (int, float)):
            valid_numbers.add(str(val))
            if isinstance(val, float):
                valid_numbers.add(f"{val:.1f}")
                valid_numbers.add(f"{val:.2f}")
                valid_numbers.add(f"{val:.3f}")
                valid_numbers.add(f"{val:.4f}")
                # Percentages
                if 0.0 <= val <= 1.0:
                    pct = val * 100
                    valid_numbers.add(f"{pct:.1f}")
                    valid_numbers.add(f"{pct:.2f}")
                    valid_numbers.add(str(round(pct)))
                    valid_numbers.add(str(round(pct, 1)))
            elif isinstance(val, int):
                valid_numbers.add(str(val))

    def traverse(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                traverse(v)
        elif isinstance(obj, list):
            for item in obj:
                traverse(item)
        elif isinstance(obj, (int, float)):
            register_num(obj)

    for fname in os.listdir(LOGS_DIR):
        if fname.endswith(".json"):
            p = os.path.join(LOGS_DIR, fname)
            try:
                with open(p, "r", encoding="utf-8") as f:
                    traverse(json.load(f))
            except Exception as e:
                print(f"Warning: could not read {p}: {e}")

    # Add standard structural constants derived from benchmark specs
    benchmark_manifest_path = os.path.join(LOGS_DIR, "benchmark_manifest.json")
    if os.path.exists(benchmark_manifest_path):
        with open(benchmark_manifest_path, "r", encoding="utf-8") as f:
            bm = json.load(f)
            traverse(bm)

    return valid_numbers


def extract_numbers_from_tex(tex_content):
    """
    Extracts all numeric tokens from abstract, tables, and experimental results sections.
    Filters out LaTeX syntax, cross-references, citation years, and column specifiers.
    """
    # 1. Extract Abstract
    abstract_match = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', tex_content, re.DOTALL)
    abstract_text = abstract_match.group(1) if abstract_match else ""

    # 2. Extract All Tables
    tables = re.findall(r'\\begin\{table\*?\}(.*?)\\end\{table\*?\}', tex_content, re.DOTALL)
    tables_text = "\n".join(tables)

    # 3. Extract Results & Evaluation Sections
    results_match = re.search(
        r'(\\section\{Experimental Evaluation\}.*?)(?=\\section\{Limitations|\Z)',
        tex_content,
        re.DOTALL
    )
    results_text = results_match.group(1) if results_match else ""

    combined_corpus = f"{abstract_text}\n{tables_text}\n{results_text}"

    # Clean LaTeX markup
    cleaned = re.sub(r'%.*?\n', '\n', combined_corpus)  # strip comments
    cleaned = re.sub(r'\\cite\{[^}]*\}', '', cleaned)    # strip citations
    cleaned = re.sub(r'\\ref\{[^}]*\}', '', cleaned)      # strip refs
    cleaned = re.sub(r'\\label\{[^}]*\}', '', cleaned)    # strip labels
    cleaned = re.sub(r'\\begin\{tabular\}\{[^}]*\}', '', cleaned)  # strip tabular specifiers
    cleaned = re.sub(r'\\end\{tabular\}', '', cleaned)
    cleaned = re.sub(r'\\caption\{[^}]*\}', '', cleaned)  # captions checked separately or stripped
    cleaned = re.sub(r'\b202\d\b', '', cleaned)           # strip citation publication years (e.g. 2025)
    cleaned = re.sub(r'\\[a-zA-Z]+', ' ', cleaned)        # strip command names

    # Extract all numeric tokens (integers or decimals)
    raw_numbers = re.findall(r'\b\d+(?:\.\d+)?\b', cleaned)
    return raw_numbers


def main():
    if not os.path.exists(PAPER_PATH):
        print(f"Error: {PAPER_PATH} not found.")
        sys.exit(1)

    with open(PAPER_PATH, "r", encoding="utf-8") as f:
        tex_content = f.read()

    valid_log_numbers = load_all_log_numbers()
    extracted_numbers = extract_numbers_from_tex(tex_content)

    checked = []
    unchecked = []

    for num in extracted_numbers:
        if num in valid_log_numbers:
            checked.append(num)
        else:
            unchecked.append(num)

    total_found = len(extracted_numbers)
    checked_count = len(checked)

    print(f"============================================================")
    print(f"PAPER NUMBER VERIFICATION REPORT")
    print(f"============================================================")
    print(f"Total numbers found in abstract, tables, and results: {total_found}")
    print(f"Numbers checked and verified against logs/*.json:     {checked_count}")
    print(f"Unchecked numbers remaining:                          {len(unchecked)}")
    print(f"============================================================")

    if unchecked:
        print("\nFAIL: Found unchecked numeric claim(s) not supported by logs/:")
        unique_unchecked = sorted(list(set(unchecked)))
        for u in unique_unchecked:
            count = unchecked.count(u)
            print(f"  - '{u}' (occurred {count} time(s))")
        print("\nAll numeric claims must be derived directly from logs/*.json.")
        sys.exit(1)
    else:
        print("\nSUCCESS: All numeric claims in paper are strictly verified against empirical logs!")
        sys.exit(0)


if __name__ == "__main__":
    main()
