# Funzioni di utility per l'estrazione e calcoli KPI (già definite precedentemente)
# utils.py
import fitz  # PyMuPDF
import pandas as pd
import plotly.express as px
from openai import OpenAI
import json

# Estrazione avanzata da PDF e Excel
def extract_financial_data(uploaded_file):
    data = {}
    if uploaded_file.name.endswith('.pdf'):
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        text = " ".join([page.get_text() for page in doc])
    elif uploaded_file.name.endswith(('.xlsx', '.xls', '.csv')):
        df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith(('.xlsx', '.xls')) else pd.read_csv(uploaded_file)
        text = df.to_string()
    else:
        text = uploaded_file.read().decode('utf-8')

    # Estrazione completa con regex per BS, P&L, Cash Flow
    import re
    patterns = {
        # Profit & Loss
        "Revenue": r"(Revenue|Ricavi)[^\d]{0,10}([\d.,]+)",
        "Cost of Sales": r"(Cost of Sales|Costo del venduto)[^\d]{0,10}([\d.,]+)",
        "Gross Profit": r"(Gross Profit|Utile lordo)[^\d]{0,10}([\d.,]+)",
        "Operating Income": r"(Operating Income|Reddito operativo)[^\d]{0,10}([\d.,]+)",
        "Net Income": r"(Net Income|Utile Netto)[^\d]{0,10}([\d.,]+)",
        "EBITDA": r"EBITDA[^\d]{0,10}([\d.,]+)",
        "Depreciation": r"(Depreciation|Ammortamenti)[^\d]{0,10}([\d.,]+)",
        "Interest Expense": r"(Interest Expense|Interessi passivi)[^\d]{0,10}([\d.,]+)",

        # Balance Sheet
        "Total Assets": r"(Total Assets|Attività Totali)[^\d]{0,10}([\d.,]+)",
        "Current Assets": r"(Current Assets|Attività correnti)[^\d]{0,10}([\d.,]+)",
        "Non-current Assets": r"(Non-current Assets|Attività non correnti)[^\d]{0,10}([\d.,]+)",
        "Equity": r"(Equity|Patrimonio Netto)[^\d]{0,10}([\d.,]+)",
        "Total Debts": r"(Total Debts|Debiti Totali)[^\d]{0,10}([\d.,]+)",
        "Current Liabilities": r"(Current Liabilities|Passività correnti)[^\d]{0,10}([\d.,]+)",
        "Non-current Liabilities": r"(Non-current Liabilities|Passività non correnti)[^\d]{0,10}([\d.,]+)",

        # Cash Flow
        "Cash Flow from Operations": r"(Cash Flow from Operations|Flusso cassa operazioni)[^\d]{0,10}([\d.,]+)",
        "Cash Flow from Investing": r"(Cash Flow from Investing|Flusso cassa investimenti)[^\d]{0,10}([\d.,]+)",
        "Cash Flow from Financing": r"(Cash Flow from Financing|Flusso cassa finanziamenti)[^\d]{0,10}([\d.,]+)",
        "Net Change in Cash": r"(Net Change in Cash|Variazione netta cassa)[^\d]{0,10}([\d.,]+)",
        "Free Cash Flow": r"(Free Cash Flow|Flusso cassa libero)[^\d]{0,10}([\d.,]+)",
    }

    for key, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                data[key] = float(matches[0][1].replace(".", "").replace(",", "."))
            except:
                data[key] = None
    return data

# Calcolo KPI avanzati e personalizzati
def calculate_kpis(data):
    kpis = {}
    try:
        kpis["ROE"] = round(data["Net Income"] / data["Equity"] * 100, 2)
        kpis["ROA"] = round(data["Net Income"] / data["Total Assets"] * 100, 2)
        kpis["Debt/Equity"] = round(data["Total Debts"] / data["Equity"], 2)
        kpis["EBITDA Margin"] = round(data["EBITDA"] / data["Revenue"] * 100, 2)
        kpis["Gross Margin"] = round(data["Gross Profit"] / data["Revenue"] * 100, 2)
        kpis["Operating Margin"] = round(data["Operating Income"] / data["Revenue"] * 100, 2)
        kpis["Current Ratio"] = round(data["Current Assets"] / data["Current Liabilities"], 2)
        kpis["Quick Ratio"] = round((data["Current Assets"] - data.get("Inventory", 0)) / data["Current Liabilities"], 2)
        kpis["Interest Coverage Ratio"] = round(data["EBITDA"] / data["Interest Expense"], 2)
        kpis["Free Cash Flow Margin"] = round(data["Free Cash Flow"] / data["Revenue"] * 100, 2)
    except Exception as e:
        pass
    return pd.DataFrame([kpis])

# Restanti funzioni (Grafici KPI, Raccomandazioni intelligenti con GPT) restano invariate
