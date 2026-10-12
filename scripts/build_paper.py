"""
Paper Build Script: scripts/build_paper.py

Executes the paper generation and verification pipeline:
1. Generates results_macros.tex and tables/*.tex from empirical logs
2. Verifies all numeric claims against logs (fails if any mismatch or missing value)
3. Verifies all bibliographic citations in references.bib
4. Compiles PDF using latexmk or tectonic if available; otherwise reports missing TeX compiler honestly.
"""

import os
import sys
import shutil
import subprocess

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PAPER_DIR = os.path.join(BASE_DIR, "docs", "paper")
MAIN_TEX = os.path.join(PAPER_DIR, "main.tex")


def run_py(script_name):
    script_path = os.path.join(BASE_DIR, "scripts", script_name)
    print(f"\n--> Running {script_name}...")
    res = subprocess.run([sys.executable, script_path], cwd=BASE_DIR)
    if res.returncode != 0:
        print(f"ERROR: {script_name} exited with code {res.returncode}")
        sys.exit(res.returncode)


def main():
    print("============================================================")
    print("TOLLGATERAG PAPER BUILD PIPELINE")
    print("============================================================")

    # Step 1: Generate macros and tables
    run_py("make_result_macros.py")

    # Step 2: Check paper numbers
    run_py("check_paper_numbers.py")

    # Step 3: Check references
    run_py("check_references.py")

    # Step 4: Attempt LaTeX compilation
    print("\n--> Checking TeX Distribution...")
    compiler = None
    if shutil.which("latexmk"):
        compiler = "latexmk"
    elif shutil.which("tectonic"):
        compiler = "tectonic"
    elif shutil.which("pdflatex"):
        compiler = "pdflatex"

    if compiler:
        print(f"Found TeX compiler: {compiler}. Compiling PDF...")
        if compiler == "latexmk":
            cmd = ["latexmk", "-pdf", "-cd", MAIN_TEX]
        elif compiler == "tectonic":
            cmd = ["tectonic", MAIN_TEX]
        else:
            cmd = ["pdflatex", "-output-directory", PAPER_DIR, MAIN_TEX]
        res = subprocess.run(cmd, cwd=PAPER_DIR)
        if res.returncode == 0:
            print(f"SUCCESS: Built {MAIN_TEX.replace('.tex', '.pdf')}")
        else:
            print(f"Compilation exited with code {res.returncode}")
    else:
        print("NOTE: No TeX distribution found on system PATH (neither latexmk, tectonic, nor pdflatex is installed).")
        print("LaTeX sources, tables, and macros have been built and verified, but PDF compilation requires installing TeX Live, MiKTeX, or tectonic.")
        print("Per project ground rules: no PDF compilation was performed; LaTeX sources and artifacts remain ready for remote/local TeX rendering.")


if __name__ == "__main__":
    main()
