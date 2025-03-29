
import streamlit as st
import pandas as pd
import fitz
import re
import io
import langdetect
from fpdf import FPDF
import openai

st.set_page_config(page_title="Audit Flow Pro+ Multilingua", layout="wide")
st.title("Audit Flow Pro+")
st.subheader("Analisi bilanci in inglese o italiano – Automatica e Intelligente")

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

def parse_financial_data(text, lang):
    keywords = {
        "RICAVI": "revenue",
        "REVENUE": "revenue",
        "UTILE": "net_income",
        "NET INCOME": "net_income",
        "PATRIMONIO": "equity",
        "EQUITY": "equity",
        "ATTIVO": "assets",
        "ASSETS": "assets",
        "EBITDA": "ebitda",
        "CASH FLOW": "cash_flow",
        "COSTI": "costs",
        "COSTS": "costs",
        "DEBITI": "debts",
        "DEBTS": "debts"
    }

    pattern = r"(RICAVI|REVENUE|UTILE NETTO|NET INCOME|EBITDA|CASH FLOW|PATRIMONIO NETTO|EQUITY|TOTALE ATTIVO|TOTAL ASSETS|COSTI|COSTS|DEBITI|DEBTS):\s*EUR?\s*([\d\.,]+)"
    matches = re.findall(pattern, text.upper())
    data = {}

    for k, v in matches:
        label = keywords.get(k.strip().upper(), k.strip().lower())
        value = float(v.replace(",", "").replace(".", "").strip())
        data[label] = value

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
    testo = f"Dati:
{data}

KPI:
{kpi}

"
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
    pdf.multi_cell(0, 10, f"Dati: {data}

KPI: {kpi}

Commento GPT:
{summary}")
    output = "auditflow_report_multilang.pdf"
    pdf.output(output)
    return output

if uploaded_file:
    bytes_file = uploaded_file.read()
    text = extract_text(bytes_file)
    lang = detect_language(text)

    st.write(f"📘 Lingua rilevata: {'Italiano' if lang == 'it' else 'English'}")
    st.text_area("📄 Testo estratto dal bilancio", text, height=300)

    data = parse_financial_data(text, lang)
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
        st.download_button("📥 Scarica il report PDF", f, file_name="auditflow_report_multilang.pdf")
