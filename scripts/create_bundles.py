"""
Artifact Bundler Script: scripts/create_bundles.py

Creates submission bundles:
1. arxiv_bundle.zip (LaTeX source, macros, tables, figures, references)
2. supplementary.zip (code snapshot, data splits, and summary JSON logs)

Guarantees:
- Strictly excludes .env, credentials, API keys
- Strictly excludes logs/llm_cache/
- Strictly excludes __pycache__, .git, venv
"""

import os
import sys
import zipfile
import re

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PAPER_DIR = os.path.join(BASE_DIR, "docs", "paper")

ARXIV_ZIP = os.path.join(BASE_DIR, "arxiv_bundle.zip")
SUPP_ZIP = os.path.join(BASE_DIR, "supplementary.zip")
RESEARCH_PAPER_ZIP = os.path.join(BASE_DIR, "research_paper_bundle.zip")


def create_arxiv_bundle():
    print(f"Creating {ARXIV_ZIP}...")
    if os.path.exists(ARXIV_ZIP):
        os.remove(ARXIV_ZIP)

    with zipfile.ZipFile(ARXIV_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        # main.tex, references.bib, results_macros.tex
        for fn in ["main.tex", "references.bib", "results_macros.tex", "AUTHORS.md", "references_verification.md"]:
            p = os.path.join(PAPER_DIR, fn)
            if os.path.exists(p):
                z.write(p, arcname=fn)

        # tables
        tables_dir = os.path.join(PAPER_DIR, "tables")
        if os.path.exists(tables_dir):
            for tfn in os.listdir(tables_dir):
                if tfn.endswith(".tex"):
                    z.write(os.path.join(tables_dir, tfn), arcname=os.path.join("tables", tfn))

        # figures
        fig_dir = os.path.join(PAPER_DIR, "figures")
        if os.path.exists(fig_dir):
            for ffn in os.listdir(fig_dir):
                if ffn.endswith((".pdf", ".png")):
                    z.write(os.path.join(fig_dir, ffn), arcname=os.path.join("figures", ffn))

    print(f"SUCCESS: Created {ARXIV_ZIP} ({os.path.getsize(ARXIV_ZIP)} bytes).")


def create_supplementary_bundle():
    print(f"Creating {SUPP_ZIP}...")
    if os.path.exists(SUPP_ZIP):
        os.remove(SUPP_ZIP)

    with zipfile.ZipFile(SUPP_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        # Code
        for root, dirs, files in os.walk(os.path.join(BASE_DIR, "tollgaterag")):
            if "__pycache__" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, BASE_DIR)
                    z.write(full_p, arcname=rel_p)

        # Scripts
        for root, dirs, files in os.walk(os.path.join(BASE_DIR, "scripts")):
            if "__pycache__" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, BASE_DIR)
                    z.write(full_p, arcname=rel_p)

        # Data
        for root, dirs, files in os.walk(os.path.join(BASE_DIR, "data")):
            for f in files:
                if f.endswith((".json", ".csv")):
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, BASE_DIR)
                    z.write(full_p, arcname=rel_p)

        # Summary JSON logs only (strictly NO llm_cache, NO .env)
        logs_dir = os.path.join(BASE_DIR, "logs")
        for f in os.listdir(logs_dir):
            if f.endswith(".json"):
                full_p = os.path.join(logs_dir, f)
                z.write(full_p, arcname=os.path.join("logs", f))

        # Tests
        for root, dirs, files in os.walk(os.path.join(BASE_DIR, "tests")):
            if "__pycache__" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, BASE_DIR)
                    z.write(full_p, arcname=rel_p)

        # Core docs & specs
        for doc in [
            "PAPER_CLAIMS.md",
            "SUBMISSION_CHECKLIST.md",
            "Makefile",
            "docs/HUMAN_ANNOTATION_GUIDE.md",
            "docs/paper/claims_registry.json"
        ]:
            p = os.path.join(BASE_DIR, doc)
            if os.path.exists(p):
                z.write(p, arcname=doc)

    print(f"SUCCESS: Created {SUPP_ZIP} ({os.path.getsize(SUPP_ZIP)} bytes).")


def verify_bundle_contents(zip_path):
    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()
        for name in names:
            if ".env" in name or "llm_cache" in name or "key" in name.lower() and not "keyboard" in name.lower():
                raise ValueError(f"CRITICAL SECURITY VIOLATION: {zip_path} contains forbidden file {name}!")
    print(f"PASS: Verified {zip_path} contains zero credentials, keys, or raw cache prompts.")


def create_research_paper_bundle():
    print(f"Creating {RESEARCH_PAPER_ZIP}...")
    if os.path.exists(RESEARCH_PAPER_ZIP):
        os.remove(RESEARCH_PAPER_ZIP)

    rp_dir = os.path.join(BASE_DIR, "research_paper")
    with zipfile.ZipFile(RESEARCH_PAPER_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(rp_dir):
            if "__pycache__" in root or ".build" in root:
                continue
            for f in files:
                if f.endswith((".tex", ".pdf", ".bib", ".json", ".md", ".py", ".png")):
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, BASE_DIR)
                    z.write(full_p, arcname=rel_p)

    print(f"SUCCESS: Created {RESEARCH_PAPER_ZIP} ({os.path.getsize(RESEARCH_PAPER_ZIP)} bytes).")


def main():
    create_arxiv_bundle()
    verify_bundle_contents(ARXIV_ZIP)
    create_supplementary_bundle()
    verify_bundle_contents(SUPP_ZIP)
    create_research_paper_bundle()
    verify_bundle_contents(RESEARCH_PAPER_ZIP)


if __name__ == "__main__":
    main()
