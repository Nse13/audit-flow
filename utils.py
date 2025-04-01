import fitz
import pytesseract
import langdetect
import pandas as pd
import re
from PIL import Image
import io
import plotly.express as px
import streamlit as st

def extract_text_from_file(file):
    name = file.name.lower()
    text = ""
    if name.endswith(".pdf"):
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            for page in doc:
                try:
                    text += page.get_text()
                except:
                    pix = page.get_pixmap()
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    text += pytesseract.image_to_string(img)
    elif name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(file)
        text = df.to_string()
    elif name.endswith(".csv"):
        df = pd.read_csv(file)
        text = df.to_string()
    return text

def detect_language(text):
    try:
        return langdetect.detect(text)
    except:
        return "unknown"

def preprocess_text(text, lang):
    return text.replace("\n", " ").replace("\r", " ").replace("  ", " ").strip()

def extract_financial_data(text, year="2024", show_debug=False):
    fields = ["revenue", "net income", "ebitda", "cash flow", "operating expenses", "total assets", "equity", "total debts", "investments"]
    data = {}
    explanations = {}

    text_lines = text.lower().split("\n")

    for field in fields:
        candidates = []
        pattern = re.compile(fr"{field}[^\d\n]*([\d.,]+)")

        for i, line in enumerate(text_lines):
            matches = pattern.findall(line)
            if matches:
                score = 0
                if "total" in line: score += 1
                if "consolidated" in line: score += 1
                if "group" in line: score += 1
                if year in line: score += 2
                if "million" in line or "billion" in line: score += 1
                if i > len(text_lines) * 0.7: score += 1  # preferiamo le ultime pagine
                candidates.append((matches[0], score, line.strip()))

        if candidates:
            best = sorted(candidates, key=lambda x: -x[1])[0]
            try:
                val = best[0].replace(",", "").replace(".", "")
                data[field.title()] = int(val)
                explanations[field.title()] = best[2]
            except:
                continue

    if show_debug and explanations:
        st.subheader("📌 Debug: frasi da cui sono stati estratti i dati")
        for k, v in explanations.items():
            st.markdown(f"**{k}** → `{v}`")

    return data

def calculate_kpis(data):
    df = pd.DataFrame([data])
    if "Net Income" in df and "Equity" in df:
        df["ROE"] = df["Net Income"] / df["Equity"]
    if "Net Income" in df and "Total Assets" in df:
        df["ROA"] = df["Net Income"] / df["Total Assets"]
    if "EBITDA" in df and "Revenue" in df:
        df["EBITDA Margin"] = df["EBITDA"] / df["Revenue"]
    return df

def generate_kpi_charts(df):
    numeric_df = df.select_dtypes(include=["number"])
    if numeric_df.empty:
        return
    melted = numeric_df.T.reset_index()
    melted.columns = ["KPI", "Valore"]
    fig = px.bar(melted, x="Valore", y="KPI", orientation="h", title="KPI principali")
    st.plotly_chart(fig, use_container_width=True)

def generate_recommendations(df, lang, use_gpt=False, api_key=None):
    if use_gpt and api_key:
        import openai
        client = openai.OpenAI(api_key=api_key)
        prompt = f"Fornisci raccomandazioni in base a questi dati:\n{df.to_string()}"
        res = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}], temperature=0.3)
        return res.choices[0].message.content
    else:
        recs = []
        if "ROE" in df.columns and df["ROE"].iloc[0] < 0.05:
            recs.append("📉 Bassa redditività del capitale proprio (ROE).")
        if "EBITDA Margin" in df.columns and df["EBITDA Margin"].iloc[0] < 0.1:
            recs.append("⚠️ Margine EBITDA ridotto: controllare i costi operativi.")
        return " ".join(recs) if recs else "✅ Tutto in ordine secondo i KPI rilevati."