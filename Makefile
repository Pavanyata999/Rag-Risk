.PHONY: reproduce test check-secrets clean paper

reproduce:
	python scripts/reproduce.py

test:
	python -m pytest tests/ -q

check-secrets:
	python scripts/check_no_secrets.py

paper:
	python scripts/make_result_macros.py
	python scripts/check_paper_numbers.py
	python scripts/check_references.py
	@powershell -Command "if (Get-Command latexmk -ErrorAction SilentlyContinue) { latexmk -pdf -cd docs/paper/main.tex } elseif (Get-Command tectonic -ErrorAction SilentlyContinue) { tectonic docs/paper/main.tex } else { Write-Host 'No TeX distribution found (neither latexmk nor tectonic available on system PATH). LaTeX sources and tables generated, but PDF compilation requires installing TeX Live, MiKTeX, or tectonic.' }"

clean:
	rm -rf __pycache__ chroma_store logs/provenance.jsonl logs/review_queue.jsonl
