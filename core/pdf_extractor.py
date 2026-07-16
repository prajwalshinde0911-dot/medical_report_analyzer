import pdfplumber

def extract_text_from_pdf(file):
    """Extract text from a digital PDF lab report."""
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

def is_text_extractable(file):
    """Check if the PDF has selectable text (not just scanned images)."""
    text = extract_text_from_pdf(file)
    return len(text.strip()) > 30  # arbitrary threshold — if very little text, likely scanned/image-based