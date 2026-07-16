import re

def parse_range(ref_range):
    """Convert a reference range string into (low, high) floats. Handles '<x' and '>x' too."""
    ref_range = ref_range.strip()

    if ref_range.startswith("<"):
        high = float(re.findall(r"[\d.]+", ref_range)[0])
        return (None, high)
    if ref_range.startswith(">"):
        low = float(re.findall(r"[\d.]+", ref_range)[0])
        return (low, None)

    numbers = re.findall(r"[\d.]+", ref_range)
    if len(numbers) == 2:
        return (float(numbers[0]), float(numbers[1]))
    return (None, None)

def get_status(value, ref_range):
    """Return 'Low', 'High', or 'Normal' based on value vs reference range."""
    try:
        value = float(value)
    except ValueError:
        return "Unknown"

    low, high = parse_range(ref_range)

    if low is not None and value < low:
        return "Low"
    if high is not None and value > high:
        return "High"
    if low is None and high is None:
        return "Unknown"
    return "Normal"

def annotate_dataframe(df):
    """Add a Status column to the parsed parameters DataFrame."""
    df = df.copy()
    df["Status"] = df.apply(lambda row: get_status(row["Result"], row["Reference Range"]), axis=1)
    return df