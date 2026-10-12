.PHONY: reproduce test check-secrets clean

reproduce:
	python scripts/reproduce.py

test:
	python -m pytest tests/ -q

check-secrets:
	python scripts/check_no_secrets.py

clean:
	rm -rf __pycache__ chroma_store logs/provenance.jsonl logs/review_queue.jsonl
