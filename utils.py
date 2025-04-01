import fitz  # PyMuPDF

def extract_text_from_file(file_bytes, filename):
    if filename.endswith(".pdf"):
        text = ""
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text
    elif filename.endswith(".txt") or filename.endswith(".json"):
        return file_bytes.decode("utf-8", errors="ignore")
    else:
        return ""

def extract_financial_data(text):
    import re
    patterns = {
        "Revenue": r"Revenue[:\s]*EUR?\s?([\d,\.]+)",
        "Net Income": r"Net Income[:\s]*EUR?\s?([\d,\.]+)",
        "EBITDA": r"EBITDA[:\s]*EUR?\s?([\d,\.]+)",
        "Total Assets": r"Total Assets[:\s]*EUR?\s?([\d,\.]+)",
        "Equity": r"Equity[:\s]*EUR?\s?([\d,\.]+)",
        "Total Debts": r"Total Debts[:\s]*EUR?\s?([\d,\.]+)",
        "Operating Costs": r"Operating Costs[:\s]*EUR?\s?([\d,\.]+)",
        "Cash Flow": r"Cash Flow[:\s]*EUR?\s?([\d,\.]+)",
        "Investments": r"Investments[:\s]*EUR?\s?([\d,\.]+)"
    }

    data = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).replace(",", "").replace(".", "")
            try:
                data[key] = int(value)
            except ValueError:
                data[key] = value
    return data