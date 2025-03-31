import fitz
import re

def extract_text_from_pdf(uploaded_file):
    text_pages = []
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        for page in doc:
            text_pages.append(page.get_text())
    return text_pages

def extract_key_values(pages):
    keywords = ["Revenue", "Net Income", "EBITDA", "Total Assets", "Equity", "Total Debts", "Cash Flow"]
    results = []
    for i, text in enumerate(pages):
        for kw in keywords:
            matches = re.findall(rf"{kw}[^\d]*(\d[\d,.]*)", text, re.IGNORECASE)
            for match in matches:
                value = match.replace(",", "").replace(".", "")
                try:
                    num = float(value)
                    results.append({"label": kw, "value": num, "context": text[:1000], "page": i})
                except:
                    continue
    return results

def calculate_kpi(data):
    kpi = {}
    if "Revenue" in data and "Net Income" in data and data["Revenue"] > 0:
        kpi["Profit Margin (%)"] = round((data["Net Income"] / data["Revenue"]) * 100, 2)
    if "EBITDA" in data and "Total Assets" in data and data["Total Assets"] > 0:
        kpi["ROA (%)"] = round((data["EBITDA"] / data["Total Assets"]) * 100, 2)
    return kpi

def generate_recommendations(kpi):
    recs = []
    if kpi.get("Profit Margin (%)", 100) < 5:
        recs.append("📉 Margine di profitto basso: ridurre costi o aumentare ricavi.")
    if kpi.get("ROA (%)", 100) < 5:
        recs.append("🏭 Basso ritorno sugli asset: migliorare efficienza operativa.")
    return recs