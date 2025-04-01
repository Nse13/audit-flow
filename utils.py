import fitz
import pandas as pd
import langdetect
import re
from collections import defaultdict
import plotly.express as px

def extract_text_from_file(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        text = ""
        with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        return text
    elif uploaded_file.name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
        return df.to_string(index=False)
    elif uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        return df.to_string(index=False)
    return ""

def detect_language(text):
    try:
        return langdetect.detect(text)
    except:
        return "unknown"

def preprocess_text(text):
    return re.sub(r"[^\w\s€\.,]", "", text)

def extract_financial_data(text):
    patterns = {
        "Revenue": r"Revenue\D+(\d+[\d.,]*)",
        "Net Income": r"Net Income\D+(\d+[\d.,]*)",
        "EBITDA": r"EBITDA\D+(\d+[\d.,]*)",
        "Total Assets": r"Total Assets\D+(\d+[\d.,]*)",
        "Equity": r"Equity\D+(\d+[\d.,]*)",
        "Total Debts": r"Total Debts\D+(\d+[\d.,]*)",
        "Cash Flow": r"Cash Flow\D+(\d+[\d.,]*)",
        "Operating Costs": r"Operating (Expenses|Costs)\D+(\d+[\d.,]*)",
        "Investments": r"Investments\D+(\d+[\d.,]*)",
        "Year": r"Year\D*(\d{4})"
    }
    data = defaultdict(list)
    for key, pattern in patterns.items():
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        for match in matches:
            value = match if isinstance(match, str) else match[-1]
            try:
                num = float(value.replace(",", "").replace(".", ""))
                data[key].append(num)
            except:
                continue
    if not data:
        return pd.DataFrame()
    if "Year" in data:
        rows = []
        for i in range(len(data["Year"])):
            row = {k: data[k][i] if i < len(data[k]) else None for k in data}
            rows.append(row)
        return pd.DataFrame(rows)
    else:
        return pd.DataFrame([{k: v[0] for k, v in data.items()}])

def calculate_kpis(df):
    kpis = {}
    if isinstance(df, pd.DataFrame):
        row = df.iloc[-1] if len(df) else df
    else:
        row = df
    try:
        kpis["ROE"] = round(row["Net Income"] / row["Equity"], 2)
    except: pass
    try:
        kpis["ROI"] = round(row["Net Income"] / row["Total Assets"], 2)
    except: pass
    try:
        kpis["Debts/Equity"] = round(row["Total Debts"] / row["Equity"], 2)
    except: pass
    try:
        kpis["EBITDA Margin"] = round(row["EBITDA"] / row["Revenue"], 2)
    except: pass
    return kpis

def generate_kpi_charts(kpis):
    df = pd.DataFrame(kpis.items(), columns=["KPI", "Value"])
    return px.bar(df, x="Value", y="KPI", orientation="h", title="KPI principali")

def analyze_trends(df):
    if "Year" in df.columns:
        return df.sort_values("Year")
    return pd.DataFrame()

def generate_recommendations(df):
    recs = []
    if isinstance(df, pd.DataFrame):
        df = df.iloc[-1]
    try:
        if df["Revenue"] < df["Total Debts"]:
            recs.append("📉 Le entrate sono inferiori ai debiti: migliorare il cash flow.")
        if df["Equity"] < df["Total Debts"]:
            recs.append("⚠️ Bassa equità rispetto ai debiti: possibile rischio finanziario.")
        if df["Net Income"] > 0:
            recs.append("✅ Redditività positiva: l'azienda genera utili.")
    except: pass
    return recs
