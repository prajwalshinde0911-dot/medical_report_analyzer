import os
import numpy as np
import streamlit as st
from pdf2image import convert_from_bytes

WINDOWS_POPPLER_PATH = r"C:\poppler\poppler-24.07.0\Library\bin"

def get_poppler_path():
    if os.name == "nt" and os.path.exists(WINDOWS_POPPLER_PATH):
        return WINDOWS_POPPLER_PATH
    return None

@st.cache_resource
def get_ocr_reader():
    import easyocr
    return easyocr.Reader(['en'], gpu=False)

def extract_text_with_ocr(file_bytes):
    """
    Extract text from a scanned/image-based PDF using OCR.
    Works locally on Windows (via Poppler path) and on Streamlit Cloud (via packages.txt).
    """
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
        results = reader.readtext(img_array, detail=0)
        full_text += "\n".join(results) + "\n"

    return full_text.strip()