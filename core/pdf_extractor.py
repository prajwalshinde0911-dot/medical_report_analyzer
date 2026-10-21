import pdfplumber


def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text += (page.extract_text() or "") + "\n"
    return text.strip()


def is_text_extractable(file, min_chars=50):
    try:
        with pdfplumber.open(file) as pdf:
            total = sum(len(page.extract_text() or "") for page in pdf.pages[:3])
        return total >= min_chars
    except Exception:
        return False