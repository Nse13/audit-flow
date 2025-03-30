
import streamlit as st
import pandas as pd
import fitz
import io
import langdetect
from fpdf import FPDF
import re
import plotly.express as px

try:
    from openai import OpenAI
    openai_available = True
except ImportError:
    openai_available = False

st.set_page_config(page_title="Audit Flow Pro+ (ibrido GPT)", layout="wide", initial_sidebar_state="expanded")
st.image("logo_auditflow.png", width=300)
st.title("Audit Flow Pro+")
st.subheader("Analisi finanziaria da PDF/Excel/CSV con o senza AI")

uploaded_file = st.sidebar.file_uploader("📂 Carica un bilancio", type=["pdf", "xlsx", "xls", "csv"])
use_gpt = st.sidebar.toggle("🔁 Usa GPT per l'analisi", value=False)
api_key = st.sidebar.text_input("🔐 API key OpenAI", type="password") if use_gpt else None

def extract_text(pdf_bytes):
    text = ""
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def detect_language(text):
    try:
        return "it" if langdetect.detect(text) == "it" else "en"
    except:
        return "en"

def extract_data_with_gpt(text, lang, api_key):
    try:
        client = OpenAI(api_key=api_key)
        prompt = f"""Analizza il testo del bilancio e restituisci i seguenti dati in formato JSON per ogni anno (se presenti):
- Total Revenue
- Net Income
- Total Assets
- Equity
- EBITDA
- Cash Flow
- Operating Costs
- Total Debts

Rispondi con JSON strutturato per anno. Testo:
{text} 
"""
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000
        )
        return pd.DataFrame(eval(response.choices[0].message.content.strip())).T
    except Exception as e:
        st.warning(f"GPT non disponibile. Errore: {e}")
        return pd.DataFrame()

def parse_data_from_text(text):
    pattern = re.compile(r"(Revenue|Net Income|Total Assets|Equity|EBITDA|Cash Flow|Operating Costs|Total Debts)[^\d]*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)", re.IGNORECASE)
    matches = pattern.findall(text)
    data = {}
    for label, value in matches:
        label = label.title().strip()
        value = value.replace(".", "").replace(",", "")
        try:
            data[label] = float(value)
        except:
            continue
    return pd.DataFrame([data], index=["2023"]) if data else pd.DataFrame()

def calculate_kpi(df):
    df_out = df.copy()
    try: df_out['ROE (%)'] = (df['Net Income'] / df['Equity']) * 100
    except: pass
    try: df_out['ROI (%)'] = (df['Net Income'] / df['Total Assets']) * 100
    except: pass
    try: df_out['Net Margin (%)'] = (df['Net Income'] / df['Revenue']) * 100
    except: pass
    try: df_out['Debt to Equity'] = df['Total Debts'] / df['Equity']
    except: pass
    try: df_out['EBITDA Margin (%)'] = df['EBITDA'] / df['Revenue'] * 100
    except: pass
    return df_out

def show_dashboard(df):
    st.subheader("📊 Dashboard KPI Interattiva")
    for col in df.columns:
        if df[col].dtype in ['float64', 'int64'] and df[col].notna().all():
            fig = px.bar(df.reset_index(), x=df.index.name or "Index", y=col, title=col)
            st.plotly_chart(fig, use_container_width=True)

def generate_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Audit Flow Pro+ Report", ln=True)
    for year, row in df.iterrows():
        pdf.multi_cell(0, 10, f"{year}: {row.to_dict()}")
    path = "/mnt/data/auditflow_report_hybrid.pdf"
    pdf.output(path)
    return path

if uploaded_file:
    file_name = uploaded_file.name
    if file_name.endswith(".pdf"):
        text = extract_text(uploaded_file.read())
        lang = detect_language(text)
        st.write(f"📘 Lingua rilevata: {'Italiano' if lang == 'it' else 'English'}")
        st.text_area("📄 Testo Estratto", text, height=300)

        if use_gpt and api_key and openai_available:
            df = extract_data_with_gpt(text, lang, api_key)
        else:
            df = parse_data_from_text(text)

    elif file_name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    elif file_name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        st.stop()

    if not df.empty:
        df.index.name = "Year"
        st.subheader("📑 Dati estratti o caricati")
        st.dataframe(df)

        df = calculate_kpi(df)
        st.subheader("📈 KPI calcolati")
        st.dataframe(df)

        show_dashboard(df)

        pdf_path = generate_pdf(df)
        with open(pdf_path, "rb") as f:
            st.download_button("📥 Scarica il report PDF", f, file_name="auditflow_report_hybrid.pdf")
    else:
        st.warning("⚠️ Nessun dato disponibile da analizzare.")
else:
    st.info("Carica un file per iniziare.")
