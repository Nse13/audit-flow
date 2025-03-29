
import streamlit as st
import pandas as pd
import fitz
import pytesseract
from PIL import Image
import langdetect
import re
import io
from fpdf import FPDF
import openai

st.set_page_config(page_title="Audit Flow Pro+", layout="wide")
st.title("Audit Flow Pro+")
st.subheader("Analisi finanziaria e Audit avanzato con AI")

uploaded_file = st.sidebar.file_uploader("📂 Carica un bilancio", type=["pdf", "xlsx", "xls"])
api_key = st.sidebar.text_input("🔐 API key OpenAI", type="password")

def extract_text(pdf_bytes, ocr=False):
    text = ""
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text() if not ocr else pytesseract.image_to_string(Image.open(io.BytesIO(page.get_pixmap().tobytes("png"))))
    return text

def parse_financial_data(text):
    matches = re.findall(r"(RICAVI|COSTI|UTILE|EBITDA|CASH FLOW|DEBITI|PATRIMONIO|ATTIVO|INTERESSI):[ ]?EUR?[ ]?([\d.,]+)", text.upper())
    return {k: float(v.replace(".", "").replace(",", "")) for k, v in matches}

def calculate_kpi(data):
    kpi = {}
    try:
        kpi["ROE"] = round(data["UTILE"] / data["PATRIMONIO"] * 100, 2)
        kpi["ROI"] = round(data["UTILE"] / data["ATTIVO"] * 100, 2)
        kpi["Margine Netto"] = round(data["UTILE"] / data["RICAVI"] * 100, 2)
    except:
        pass
    return kpi

def gpt_summary(data, kpi, api_key):
    openai.api_key = api_key
    prompt = f"Sintesi audit:\nDati: {data}\nKPI: {kpi}\nSintesi professionale in italiano."
    return openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}], max_tokens=200).choices[0].message["content"]

def generate_pdf(data, kpi, summary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Report Audit Flow Pro+", ln=True)
    pdf.multi_cell(0, 10, f"Dati finanziari: {data}\nKPI: {kpi}\nCommento AI: {summary}")
    output = "/mnt/data/audit_flow_report_final.pdf"
    pdf.output(output)
    return output

if uploaded_file:
    bytes_file = uploaded_file.read()
    text = extract_text(bytes_file, ocr=True)
    st.text_area("Testo Estratto", text, height=250)

    data = parse_financial_data(text)
    st.json(data)

    kpi = calculate_kpi(data)
    st.json(kpi)

    if api_key:
        summary = gpt_summary(data, kpi, api_key)
        st.success(summary)
        pdf_path = generate_pdf(data, kpi, summary)
        with open(pdf_path, "rb") as f:
            st.download_button("📥 Scarica Report", f, "AuditFlow_Report.pdf")
    else:
        st.warning("Inserisci API key OpenAI per generare il report completo.")
