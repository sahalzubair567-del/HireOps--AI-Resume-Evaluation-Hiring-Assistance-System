from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF
from docx import Document


def extract_text(file_path: str, filename: str) -> str:
  """
  Extract raw text from a resume file.

  - PDF files are read with PyMuPDF (fitz) across all pages.
  - DOCX files are read with python-docx by joining all paragraphs.
  - On any failure, returns an empty string "".
  """
  path = Path(file_path)
  name_lower = filename.lower()

  try:
    if name_lower.endswith(".pdf"):
      text_chunks: list[str] = []
      with fitz.open(path) as doc:
        for page in doc:
          text_chunks.append(page.get_text() or "")
      return "\n".join(text_chunks).strip()

    if name_lower.endswith(".docx"):
      document = Document(str(path))
      paragraphs = [p.text for p in document.paragraphs if p.text]
      return "\n".join(paragraphs).strip()
  except Exception:
    return ""

  # Unsupported extension: return empty string as a safe default
  return ""

