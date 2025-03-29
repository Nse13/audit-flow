
import streamlit as st
import pandas as pd
import fitz
import io
import langdetect
from fpdf import FPDF
import openai

st.set_page_config(page_title="Audit Flow Pro+ GPT Expert", layout="wide")
st.title("Audit Flow Pro+ GPT Expert")
st.subheader("Analisi finanziaria avanzata con ragionamento GPT e precisione sui dati")

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

def extract_structured_data_with_gpt(text, lang, api_key):
    client = openai.OpenAI(api_key=api_key)
    if lang == "it":
        prompt = f"""Analizza il seguente testo di bilancio e restituisci solo i valori principali in formato JSON:
- Ricavi totali (revenue)
- Utile netto (net income)
- Totale attivo (assets)
- Patrimonio netto (equity)
- EBITDA
- Cash Flow
- Costi operativi (costs)
- Debiti totali (debts)

Testo bilancio:
{text}

Rispondi solo con il JSON, senza spiegazioni."""
    else:
        prompt = f"""Analyze the following financial report text and return only the key financial values in JSON format:
- Total Revenue
- Net Income
- Total Assets
- Equity
- EBITDA
- Cash Flow
- Operating Costs
- Total Debts

Report text:
{text}

Respond with only JSON, no explanations."""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=500
    )

    import json
    try:
        raw_json = response.choices[0].message.content.strip()
        data = json.loads(raw_json)
        return {k: float(str(v).replace(",", "").replace("€", "").strip()) for k, v in data.items()}
    except:
        return {}

def calculate_kpi(data):
    kpi = {}
    try:
        kpi["ROE (%)"] = round((data["Net Income"] / data["Equity"]) * 100, 2)
        kpi["ROI (%)"] = round((data["Net Income"] / data["Total Assets"]) * 100, 2)
        kpi["Net Margin (%)"] = round((data["Net Income"] / data["Total Revenue"]) * 100, 2)
    except:
        pass
    return kpi

def generate_pdf(data, kpi, summary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Audit Flow Pro+ Expert Report", ln=True)
    pdf.multi_cell(0, 10, f"Dati Estratti: {data}\n\nKPI: {kpi}\n\nSintesi GPT:\n{summary}")
    output = "auditflow_report_gpt_expert.pdf"
    pdf.output(output)
    return output

def gpt_summary(data, kpi, lang, api_key):
    client = openai.OpenAI(api_key=api_key)
    testo = (
        f"Dati:
{data}

"
        f"KPI:
{kpi}

"
    )
    if lang == "it":
        prompt = "Agisci come un revisore contabile e fornisci una sintesi professionale in italiano del bilancio seguente. " + testo
    else:
        prompt = "Act as an auditor and provide a professional English summary of the financial report below. " + testo

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.3
    )

    return response.choices[0].message.content

if uploaded_file:
    if not api_key:
        st.warning("Inserisci la tua OpenAI API key per usare l’analisi GPT.")
    else:
        bytes_file = uploaded_file.read()
        text = extract_text(bytes_file)
        lang = detect_language(text)

        st.write(f"📘 Lingua rilevata: {'Italiano' if lang == 'it' else 'English'}")
        st.text_area("📄 Testo estratto dal bilancio", text, height=300)

        data = extract_structured_data_with_gpt(text, lang, api_key)
        kpi = calculate_kpi(data)

        st.subheader("📊 Dati finanziari estratti (da GPT)")
        st.json(data)

        st.subheader("📈 KPI Calcolati")
        st.json(kpi)

        summary = gpt_summary(data, kpi, lang, api_key)
        st.success(summary)

        pdf_path = generate_pdf(data, kpi, summary)
        with open(pdf_path, "rb") as f:
            st.download_button("📥 Scarica il report PDF", f, file_name="auditflow_report_gpt_expert.pdf")
