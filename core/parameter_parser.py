import re
import pandas as pd

def parse_parameters(text):
    """
    Parse lab report text and extract test parameters.
    Expects lines roughly like:
    Hemoglobin (Hb)    11.2    g/dL    13.5 - 17.5
    """
    results = []

    # Pattern: name ... number ... unit ... range (number - number)
    pattern = re.compile(
        r"([A-Za-z][A-Za-z0-9\s\(\)/%]+?)\s+"     # test name
        r"([\d.]+)\s+"                             # result value
        r"([a-zA-Z/%µ]+(?:\s*cumm)?)\s+"           # unit
        r"([<>]?\s*[\d.]+\s*-?\s*[\d.]*)"          # reference range
    )

    for line in text.split("\n"):
        line = line.strip()
        if not line or len(line) < 10:
            continue

        match = pattern.search(line)
        if match:
            name = match.group(1).strip()
            value = match.group(2).strip()
            unit = match.group(3).strip()
            ref_range = match.group(4).strip()

            # Skip header-like lines
            if name.lower() in ["test name", "reference range"]:
                continue

            results.append({
                "Parameter": name,
                "Result": value,
                "Unit": unit,
                "Reference Range": ref_range
            })

    return pd.DataFrame(results)
