import pdfplumber

def extract_text_from_pdf(file):
    """Extract text from a digital PDF lab report."""
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        # Surface the real underlying error instead of letting it crash the whole app
        return f"[PDF_ERROR] Could not read PDF: {type(e).__name__}: {e}"
    return text.strip()

def is_text_extractable(file):
    """Check if the PDF has selectable text (not just scanned images)."""
    text = extract_text_from_pdf(file)
    if text.startswith("[PDF_ERROR]"):
        # Treat unreadable-as-text PDFs as "not extractable" so the app
        # falls through to the OCR path instead of crashing.
        return False
    return len(text.strip()) > 30  # arbitrary threshold — if very little text, likely scanned/image-based