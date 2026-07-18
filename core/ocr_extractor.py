import easyocr
import numpy as np
from pdf2image import convert_from_bytes

reader = easyocr.Reader(['en'], gpu=False)

POPPLER_PATH = r"C:\poppler\poppler-24.07.0\Library\bin"


def extract_text_with_ocr(file_bytes, row_tolerance=12):
    """
    Extract text from a scanned/image-based PDF using OCR,
    reconstructing table rows from bounding-box positions so
    values stay on the same line as their parameter/unit/range.
    """
    images = convert_from_bytes(file_bytes, poppler_path=POPPLER_PATH)
    full_text = ""

    for img in images:
        img_array = np.array(img)
        # detail=1 keeps bounding boxes: (bbox, text, confidence)
        results = reader.readtext(img_array, detail=1)

        # Each bbox is 4 corner points; use the top-left y as row position,
        # top-left x as column position for left-to-right ordering.
        items = []
        for bbox, text, conf in results:
            x = bbox[0][0]
            y = bbox[0][1]
            items.append((y, x, text))

        # Sort top-to-bottom, then left-to-right
        items.sort(key=lambda t: (t[0], t[1]))

        # Group into rows: items whose y is within row_tolerance are same line
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
            row.sort(key=lambda t: t[0])  # left-to-right within the row
            full_text += "    ".join(text for _, text in row) + "\n"

    return full_text.strip()