import fitz
import re
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

def extract_text_from_pdf(path):
    doc = fitz.open(path)
    return " ".join([page.get_text() for page in doc])

def extract_financial_data(path, return_debug=False):
    text = extract_text_from_pdf(path)
    patterns = {
        "Revenue": r"(Revenue|Ricavi)[^\d]{0,10}([\d.,]+)",
        "Net Income": r"(Net Income|Utile Netto)[^\d]{0,10}([\d.,]+)",
        "EBITDA": r"(EBITDA)[^\d]{0,10}([\d.,]+)",
        "Total Assets": r"(Total Assets|Attività Totali)[^\d]{0,10}([\d.,]+)",
        "Equity": r"(Equity|Patrimonio Netto)[^\d]{0,10}([\d.,]+)",
        "Total Debts": r"(Total Debts|Debiti Totali)[^\d]{0,10}([\d.,]+)",
        "Operating Costs": r"(Operating Costs|Costi Operativi)[^\d]{0,10}([\d.,]+)",
        "Cash Flow": r"(Cash Flow|Flusso di cassa)[^\d]{0,10}([\d.,]+)",
        "Investments": r"(Investments|Investimenti)[^\d]{0,10}([\d.,]+)",
    }

    data = {}
    debug = {}

    for key, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        cleaned = []
        for match in matches:
            try:
                number = float(match[1].replace(".", "").replace(",", "."))
                if number > 1000:  # Filtro euristico per evitare numeri tipo "pagina 2"
                    cleaned.append((match[0], number))
            except:
                continue
        if cleaned:
            # Prendi il primo match valido
            data[key] = cleaned[0][1]
            debug[key] = f"{cleaned[0][0]} -> {cleaned[0][1]}"
        else:
            debug[key] = "❌ Nessun valore rilevato"

    if return_debug:
        return data, debug
    return data

def calculate_kpis(data):
    kpis = {}
    try:
        kpis["ROE"] = round(data["Net Income"] / data["Equity"] * 100, 2)
    except: pass
    try:
        kpis["ROA"] = round(data["Net Income"] / data["Total Assets"] * 100, 2)
    except: pass
    try:
        kpis["Debt/Equity"] = round(data["Total Debts"] / data["Equity"], 2)
    except: pass
    try:
        kpis["EBITDA Margin"] = round(data["EBITDA"] / data["Revenue"] * 100, 2)
    except: pass
    try:
        kpis["Operating Margin"] = round((data["Revenue"] - data["Operating Costs"]) / data["Revenue"] * 100, 2)
    except: pass
    return pd.DataFrame([kpis])

def plot_kpis(df):
    if not df.empty:
        df.T.plot(kind="barh", legend=False)
        st.pyplot(plt.gcf())