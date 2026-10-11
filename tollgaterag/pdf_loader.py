"""Turn a real (text-based) PDF into a corpus document with an explicit trust label.

    python -m tollgaterag.pdf_loader file.pdf verified official_docs

Scanned/image-only PDFs need OCR first (not included).
"""

import os
import sys
from datetime import date

from pypdf import PdfReader

from tollgaterag import config


def extract_text_from_pdf(path: str) -> str:
    return "\n".join((p.extract_text() or "") for p in PdfReader(path).pages).strip()


def ingest_pdf(pdf_path, trust_level="unverified", source="pdf_upload", doc_date=None, title=None) -> str:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(pdf_path)
    body = extract_text_from_pdf(pdf_path)
    if not body:
        raise ValueError("No extractable text (scanned PDF?). OCR is not included.")
    base = os.path.splitext(os.path.basename(pdf_path))[0]
    out = os.path.join(config.DATA_DIR, f"pdf_{base}.txt")
    header = (f"SOURCE: {source}\nTRUST_LEVEL: {trust_level}\n"
              f"DATE: {doc_date or date.today().isoformat()}\nTITLE: {title or base}\n\n")
    with open(out, "w", encoding="utf-8") as f:
        f.write(header + body)
    print(f"Saved {out} ({len(body)} chars). Now run: python -m tollgaterag.ingest")
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m tollgaterag.pdf_loader <file.pdf> [trust_level] [source]")
        sys.exit(1)
    ingest_pdf(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "unverified",
               sys.argv[3] if len(sys.argv) > 3 else "pdf_upload")
