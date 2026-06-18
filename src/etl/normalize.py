import re

def normalize_ticker(ticker):
    """Clean a company ticker: strip whitespace/newlines, uppercase it."""
    if not isinstance(ticker, str):
        return ticker
    return ticker.strip().upper()

def normalize_year(year_value):
    """Convert various year formats into a standard 'YYYY-MM' string."""
    if year_value is None:
        return None

    text = str(year_value).strip()

    # Already in correct format, e.g. "2023-03"
    if re.match(r"^\d{4}-\d{2}$", text):
        return text

    # Formats like "Mar-23", "Mar 23", "Dec-22"
    month_map = {
        "jan": "01", "feb": "02", "mar": "03", "apr": "04",
        "may": "05", "jun": "06", "jul": "07", "aug": "08",
        "sep": "09", "oct": "10", "nov": "11", "dec": "12",
    }
    match = re.match(r"^([A-Za-z]{3})[\s\-]?(\d{2,4})$", text)
    if match:
        month_str = match.group(1).lower()
        year_str = match.group(2)
        if month_str in month_map:
            if len(year_str) == 2:
                year_str = "20" + year_str
            return f"{year_str}-{month_map[month_str]}"

    # Format like "FY23" or "FY2023"
    match = re.match(r"^FY(\d{2,4})$", text, re.IGNORECASE)
    if match:
        year_str = match.group(1)
        if len(year_str) == 2:
            year_str = "20" + year_str
        return f"{year_str}-03"  # FY label alone assumes March year-end

    # Plain year like "2023"
    if re.match(r"^\d{4}$", text):
        return f"{text}-03"

    # Could not parse - flag it
    return "PARSE_ERROR"
