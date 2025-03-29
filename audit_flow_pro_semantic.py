
import streamlit as st
import pandas as pd
import fitz
import re
import io
import langdetect
from fpdf import FPDF
import openai
from difflib import get_close_matches

st.set_page_config(page_title="Audit Flow Pro+ Semantico", layout="wide")
st.title("Audit Flow Pro+")
st.subheader("Analisi semantica bilanci in inglese o italiano – flessibile e intelligente")

uploaded_file = st.sidebar.file_uploader("📂 Carica un bilancio PDF", type=["pdf"])
api_key = st.sidebar.text_input("🔐 API key OpenAI", type="password")

def extract_text(pdf_bytes):
    text = ""
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def detect_language(text):
    try:
        lang = langdetect.detect(text)
        return "it" if lang == "it" else "en"
    except:
        return "en"

# Dizionario flessibile con sinonimi
semantic_keywords = {
    "revenue": ["revenue", "total revenue", "sales", "turnover", "ricavi", "fatturato"],
    "net_income": ["net income", "profit", "net profit", "utile netto", "result"],
    "equity": ["equity", "patrimonio netto", "shareholders' equity"],
    "assets": ["assets", "total assets", "attivo", "attività"],
    "ebitda": ["ebitda", "gross margin", "margine operativo lordo"],
    "cash_flow": ["cash flow", "flusso di cassa", "net cash"],
    "costs": ["costs", "expenses", "operating expenses", "costi", "spese"],
    "debts": ["debts", "liabilities", "debt", "debiti", "obbligazioni"]
}

def match_semantic_label(label):
    label = label.lower()
    for key, synonyms in semantic_keywords.items():
        if label in synonyms:
            return key
        # Matching approssimato (es. "revenus" → "revenue")
        close = get_close_matches(label, synonyms, n=1, cutoff=0.85)
        if close:
            return key
    return None

def parse_financial_data(text):
    pattern = r"(.*?)\s*[:\-]?\s*(€|EUR)?\s*([\d\.,]+)"
    matches = re.findall(pattern, text.upper())
    data = {}

    for label, _, value in matches:
        key = match_semantic_label(label.strip())
        if key:
            try:
                val = float(value.replace(",", "").replace(".", "").strip())
                data[key] = val
            except:
                continue
    return data

def calculate_kpi(data):
    kpi = {}
    try:
        kpi["ROE (%)"] = round((data["net_income"] / data["equity"]) * 100, 2)
        kpi["ROI (%)"] = round((data["net_income"] / data["assets"]) * 100, 2)
        kpi["Margine netto (%)"] = round((data["net_income"] / data["revenue"]) * 100, 2)
    except:
        pass
    return kpi

def gpt_summary(data, kpi, lang, api_key):
    client = openai.OpenAI(api_key=api_key)
    testo = f"Dati:\n{data}\n\nKPI:\n{kpi}\n\n"
    if lang == "it":
        prompt = "Agisci come un revisore contabile e fornisci una sintesi professionale in italiano del bilancio seguente. " + testo
    else:
        prompt = "Act as an auditor and provide a professional English summary of the financial report below. " + testo

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.4
    )

    return response.choices[0].message.content

def generate_pdf(data, kpi, summary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Audit Flow Pro+ Report", ln=True)
    pdf.multi_cell(0, 10, f"Dati: {data}\n\nKPI: {kpi}\n\nCommento GPT:\n{summary}")
    output = "auditflow_report_semantic.pdf"
    pdf.output(output)
    return output

if uploaded_file:
    bytes_file = uploaded_file.read()
    text = extract_text(bytes_file)
    lang = detect_language(text)

    st.write(f"📘 Lingua rilevata: {'Italiano' if lang == 'it' else 'English'}")
    st.text_area("📄 Testo estratto dal bilancio", text, height=300)

    data = parse_financial_data(text)
    kpi = calculate_kpi(data)

    st.subheader("📊 Dati estratti")
    st.json(data)

    st.subheader("📈 KPI Calcolati")
    st.json(kpi)

    if api_key:
        summary = gpt_summary(data, kpi, lang, api_key)
    else:
        summary = "API key non inserita: commento GPT non disponibile."

    st.success(summary)
    pdf_path = generate_pdf(data, kpi, summary)
    with open(pdf_path, "rb") as f:
        st.download_button("📥 Scarica il report PDF", f, file_name="auditflow_report_semantic.pdf")
