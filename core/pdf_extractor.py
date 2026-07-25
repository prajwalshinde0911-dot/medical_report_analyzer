import pdfplumber
import PyPDF2


def _extract_with_pdfplumber(file):
    text = ""
    file.seek(0)
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()


def _extract_with_pypdf2(file):
    text = ""
    file.seek(0)
    reader = PyPDF2.PdfReader(file)
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()


def extract_text_from_pdf(file):
    """
    Extract text from a digital PDF lab report.
    Tries pdfplumber first, falls back to PyPDF2 if that fails.
    """
    try:
        text = _extract_with_pdfplumber(file)
        if text:
            return text
    except Exception:
        pass

    try:
        text = _extract_with_pypdf2(file)
        if text:
            return text
    except Exception:
        pass

    return ""


def is_text_extractable(file):
    """Check if the PDF has selectable text (not just scanned images)."""
    text = extract_text_from_pdf(file)
    return len(text.strip()) > 30