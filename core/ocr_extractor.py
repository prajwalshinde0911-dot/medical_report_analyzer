import os
import shutil
import numpy as np
import streamlit as st
from pdf2image import convert_from_bytes

WINDOWS_POPPLER_PATH = r"C:\poppler\poppler-24.07.0\Library\bin"


def get_poppler_path():
    """Return an explicit poppler bin path on Windows, or None to rely on system PATH (Linux/Cloud)."""
    if os.name == "nt" and os.path.exists(WINDOWS_POPPLER_PATH):
        return WINDOWS_POPPLER_PATH
    return None


def check_poppler_available(poppler_path=None):
    """
    Verify that poppler's command-line tools (pdftoppm / pdfinfo) can actually
    be found, so we can fail with a clear message instead of a cryptic one.
    """
    if poppler_path:
        pdftoppm = os.path.join(poppler_path, "pdftoppm")
        pdfinfo = os.path.join(poppler_path, "pdfinfo")
        found = os.path.exists(pdftoppm) or os.path.exists(pdftoppm + ".exe")
    else:
        found = shutil.which("pdftoppm") is not None and shutil.which("pdfinfo") is not None

    return found


@st.cache_resource
def get_ocr_reader():
    import easyocr
    return easyocr.Reader(['en'], gpu=False)


def extract_text_with_ocr(file_bytes, row_tolerance=12):
    """
    Extract text from a scanned/image-based PDF using OCR, reconstructing
    table rows from bounding-box positions so values stay on the same line
    as their parameter/unit/range.

    Returns a plain string. On failure, returns a string starting with
    "[OCR_ERROR]" so the caller can detect and surface the problem clearly.
    """
    poppler_path = get_poppler_path()

    if not check_poppler_available(poppler_path):
        return (
            "[OCR_ERROR] Poppler is not installed or not found in PATH on this server. "
            "This is a system dependency issue (not related to the PDF content). "
            "Add a 'packages.txt' file to your repo root containing the line "
            "'poppler-utils' and redeploy."
        )

    try:
        images = convert_from_bytes(file_bytes, poppler_path=poppler_path)
    except Exception as e:
        return f"[OCR_ERROR] Could not convert PDF pages to images: {e}"

    if not images:
        return "[OCR_ERROR] PDF converted but produced 0 pages — the file may be corrupt or empty."

    try:
        reader = get_ocr_reader()
    except Exception as e:
        return f"[OCR_ERROR] OCR engine (EasyOCR) failed to load: {e}"

    full_text = ""
    for img in images:
        img_array = np.array(img)

        try:
            results = reader.readtext(img_array, detail=1)
        except Exception as e:
            return f"[OCR_ERROR] OCR failed while reading a page: {e}"

        items = []
        for bbox, text, conf in results:
            x = bbox[0][0]
            y = bbox[0][1]
            items.append((y, x, text))
        items.sort(key=lambda t: (t[0], t[1]))

        rows = []
        current_row = []
        current_y = None
        for y, x, text in items:
            if current_y is None or abs(y - current_y) <= row_tolerance:
                current_row.append((x, text))
                current_y = y if current_y is None else current_y
            else:
                rows.append(current_row)
                current_row = [(x, text)]
                current_y = y
        if current_row:
            rows.append(current_row)

        for row in rows:
            row.sort(key=lambda t: t[0])
            full_text += "    ".join(text for _, text in row) + "\n"

    if not full_text.strip():
        return "[OCR_ERROR] OCR ran successfully but detected no text on any page."

    return full_text.strip()