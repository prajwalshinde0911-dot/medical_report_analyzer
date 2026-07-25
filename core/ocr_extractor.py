import os
import shutil
import numpy as np
import streamlit as st
from pdf2image import convert_from_bytes

WINDOWS_POPPLER_PATH = r"C:\poppler\poppler-24.07.0\Library\bin"
LINUX_FALLBACK_PATHS = ["/usr/bin", "/usr/local/bin"]


def get_poppler_path():
    if os.name == "nt" and os.path.exists(WINDOWS_POPPLER_PATH):
        return WINDOWS_POPPLER_PATH

    if shutil.which("pdftoppm") and shutil.which("pdfinfo"):
        return None

    for candidate in LINUX_FALLBACK_PATHS:
        if os.path.exists(os.path.join(candidate, "pdftoppm")) and \
           os.path.exists(os.path.join(candidate, "pdfinfo")):
            return candidate

    return None


@st.cache_resource
def get_ocr_reader():
    import easyocr
    return easyocr.Reader(['en'], gpu=False)


def extract_text_with_ocr(file_bytes, row_tolerance=12):
    try:
        reader = get_ocr_reader()
    except Exception as e:
        return f"[OCR unavailable right now: {e}]"

    try:
        poppler_path = get_poppler_path()
        images = convert_from_bytes(file_bytes, poppler_path=poppler_path)
    except Exception as e:
        return f"[Could not process scanned PDF: {e}]"

    full_text = ""
    for img in images:
        img_array = np.array(img)
        results = reader.readtext(img_array, detail=1)

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

    return full_text.strip()