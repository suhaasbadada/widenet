import io

import pdfplumber
from docx import Document


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract plain text from a PDF file.

    Uses pdfplumber which handles multi-column layouts and embedded fonts
    better than pure text-extraction libraries. Pages are joined with a
    newline so paragraph boundaries are preserved.
    """
    text_parts: list[str] = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    return "\n".join(text_parts).strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract plain text from a DOCX file.

    Iterates over paragraphs in document order. Tables and headers are
    intentionally skipped for MVP — raw paragraph text is sufficient for
    resume parsing.
    """
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs).strip()


def extract_text(file_bytes: bytes, content_type: str) -> str:
    """Dispatch text extraction based on MIME type.

    Raises ValueError for unsupported file types so the caller can return
    a clean 400 rather than a generic 500.
    """
    if content_type == "application/pdf":
        return extract_text_from_pdf(file_bytes)

    if content_type in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ):
        return extract_text_from_docx(file_bytes)

    raise ValueError(f"Unsupported file type: {content_type}. Only PDF and DOCX are accepted.")
