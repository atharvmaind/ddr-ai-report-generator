"""Load PDFs and expose raw text and page count. Uses pdfplumber for text."""

from pathlib import Path

import pdfplumber


def load_pdf_text(pdf_path: str | Path) -> dict[int, str]:
    """
    Load a PDF and return a mapping of 1-based page number -> extracted text.

    Uses pdfplumber for reliable text extraction. Returns empty string for
    pages with no text.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Not a PDF file: {path}")

    result: dict[int, str] = {}
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            result[i] = (text or "").strip()
    return result


def get_pdf_page_count(pdf_path: str | Path) -> int:
    """Return the number of pages in the PDF."""
    path = Path(pdf_path)
    with pdfplumber.open(path) as pdf:
        return len(pdf.pages)
