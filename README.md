# TollgateRAG

**Auditable pre-generation risk gating for agentic RAG, using authority-claim and verified-anchor conflict signals**

TollgateRAG sits between retrieval and generation. For every retrieved document it
computes a transparent risk score, decides **accept / warn / reject**, keeps rejected
documents out of the LLM context, writes a full audit record, and queues flagged
documents for human review.

## What is different from existing RAG defenses

Prior work in this space is crowded (e.g. RAGShield, AegisRAG-RADMS, TriShieldRAG,
MAP-Graph, source-risk triage, TrustRAG). TollgateRAG does **not** claim to be first
or the strongest. Its specific angle:

| Idea | What it does |
|---|---|
| **Unauthorized authority claim** | An *unverified* source that speaks with policy authority ("effective immediately", "supersedes", "no longer required") is penalized. Verified sources are not. |
| **Verified-anchor conflict** | An unverified source is compared against the **whole verified set** (not just what was retrieved). If it covers the same topic but *relaxes* a constraint the anchor imposes (removes an approval, a cap, a requirement), it is flagged — even with zero injection phrasing. |
| **Evaluation that measures false positives** | Corpus labels include *benign unverified* documents, so a filter that simply blocks everything unverified is exposed (it scores 100% false positives here). |
| **Context-level metric** | "Contamination" = fraction of queries whose final top-k context contains an adversarial document. |
| **Honest failure reporting** | An evasive attack and a brittle threshold are reported, not hidden. |
| **Human review queue** | Warned/rejected documents go to `logs/review_queue.jsonl` (shown in the app). |

Weaknesses relative to related work: trust labels are **self-declared** (RAGShield uses
cryptographic attestation), detectors are **cue-based heuristics**, and the evaluation
corpus is **small and authored by us** (see Limitations).

## Pipeline

```
query -> retrieve top-6 -> score 5 risk signals -> gate (accept/warn/reject)
      -> top-3 usable docs -> LLM (or offline extractive) -> audit log + review queue
```

Risk signals (weights in `tollgaterag/config.py`): trust_level 0.25, freshness 0.10,
injection 0.30, authority_claim 0.15, anchor_conflict 0.20.
Thresholds: reject >= 0.45, warn >= 0.25. Profiles: strict / balanced / lenient.

## Setup (macOS / Linux)

```bash
cd tollgaterag
python3 -m venv venv
source venv/bin/activate          # prompt must now show (venv)
pip install -r requirements.txt
python -m tollgaterag.ingest      # builds the index (13 documents)
```

Run everything **inside the activated venv**, from the project folder.

```bash
python -m tollgaterag.pipeline "What's the real travel policy, is there an unlimited allowance?"
python -m tollgaterag.eval          # main results table + per-document behaviour
python -m tollgaterag.ablation      # ablation + threshold sweep
python -m tollgaterag.excel_export  # logs/tollgaterag_metrics.xlsx (8 sheets)
streamlit run app.py                # demo UI
pytest tests/ -q                    # 9 tests
```

### Troubleshooting (issues seen on Macs)

- **`command not found: python`** — use `python3`, or activate the venv first (then `python` works).
- **`ModuleNotFoundError: chromadb`** — you are not in the activated venv, or ran `pip` for a different Python. Activate the venv and re-run `pip install -r requirements.txt`.
- **`source: no such file venv/bin/activate`** — the venv was not created in *this* folder. Run `python3 -m venv venv` here.
- **`tokenizers` build error with Python 3.14** — use Python 3.12 or 3.13: `python3.12 -m venv venv`.
- **Folder name has a space** — quote it: `cd ~/Documents/"my folder"`.
- **"Failed to send telemetry event"** — harmless Chroma message; ignore.
- **`No fitted vectorizer found`** — run `python -m tollgaterag.ingest` first.

## Using your own documents

Put `.txt` files in `data/sample_docs/` with this header, then re-run ingest:

```
SOURCE: official_docs
TRUST_LEVEL: verified          # verified | unverified | unknown
DATE: 2026-06-01
TITLE: Some title

Body text...
```

For PDFs: `python -m tollgaterag.pdf_loader file.pdf verified official_docs`
(text PDFs only; scanned PDFs need OCR). To evaluate on your corpus, add each file to
`data/labels.json` as `verified | benign | low_quality | adversarial`.

## Real LLM (optional, e.g. Ollama)

```bash
ollama pull llama3 && ollama serve
export TOLLGATERAG_LLM_BASE_URL="http://localhost:11434/v1"
export TOLLGATERAG_LLM_API_KEY="ollama"
export TOLLGATERAG_LLM_MODEL="llama3"
```

## Results (13 documents, 11 queries, top-3 context)

Corpus: 4 verified, 2 benign unverified, 1 low-quality, 6 adversarial (1 obvious
injection, 4 "policy relaxation" notes, 1 evasive document with no cue words).

| Policy | Adv. reject | Benign false-positive | Contamination | Adv. docs in context |
|---|---|---|---|---|
| Plain RAG (no gate) | 0% | 0% | 100% (11/11) | 17 |
| Trust-label filter only | 100% | **100%** | 0% | 0 |
| Injection-keyword filter only | 22.2% | 0% | 100% | 17 |
| 3-signal (trust+fresh+injection) | 22.2% | 0% | 100% | 12 |
| **TollgateRAG (5 signals)** | **88.9%** | **0%** | **27.3% (3/11)** | **3** |

Average latency 37.7 ms (offline mode; add LLM time when connected).

**Ablation (reject rate):** removing `authority_claim` or `anchor_conflict` each drops it
to 22.2%; removing `trust_level` drops it to 52.8%; removing `freshness` or
`injection` does not change it on this corpus.

## Limitations (read before citing any number)

1. **Small, self-authored corpus.** The adversarial documents were written by the
   developer *knowing the cue lists*. Results are optimistic and say little about a
   real attacker.
2. **Evasive attack succeeds.** `doc_013` states false figures with no relaxation,
   authority, or injection cues and is never rejected. This causes all 3 contaminated
   queries.
3. **Brittle reject boundary.** Subtle attacks score 0.46–0.49 against a 0.45 reject
   threshold. At reject >= 0.50 the reject rate collapses to 22.2% (they are still
   *flagged* as warn). The threshold was fixed a priori but never calibrated on
   held-out data; on 13 documents it cannot be.
4. **Self-declared trust labels.** An attacker who controls the label defeats the
   system. Cryptographic attestation would be needed in production.
5. **Cue-based, English-only detectors** — paraphrase and other languages will evade.
6. **TF-IDF retrieval** and extractive answers; no LLM-judged answer quality yet.
7. **Ablation caveat:** weights are renormalized after removal, which shifts scores.
8. No adaptive-attacker evaluation; single-turn retrieval gating only (no tool calls).

## Next steps that would make this publishable

- Held-out evaluation on an established poisoning benchmark and a larger corpus.
- Replace cue lists with a learned classifier; add an adaptive attacker.
- Calibrate thresholds on a validation split; report confidence intervals.
- Add answer-quality metrics (e.g. RAGAS) and a real embedding model.

## Layout

```
tollgaterag/   config, embeddings, ingest, retriever, risk_scorer, action_gate,
               provenance, llm_client, pipeline, eval, ablation, pdf_loader, excel_export
data/          sample_docs/ (13 .txt) and labels.json
tests/         test_tollgaterag.py
app.py         Streamlit demo
```

MIT licensed.
