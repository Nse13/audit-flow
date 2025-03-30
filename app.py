
import streamlit as st
import pandas as pd
import fitz
import io
import langdetect
from fpdf import FPDF
from openai import OpenAI
import json
import plotly.express as px

st.set_page_config(page_title="Audit Flow Pro+ Expert", layout="wide")
st.title("Audit Flow Pro+ Expert")
st.subheader("Analisi finanziaria avanzata con KPI intelligenti e GPT")

uploaded_file = st.sidebar.file_uploader("📂 Carica un bilancio PDF, Excel o CSV", type=["pdf", "xlsx", "xls", "csv"])
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

def extract_data_with_gpt(text, lang, api_key):
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
- Training Completed (%)
- Recidiva NC (%)
- Audit Duration (days)
- Risk Probability
- Risk Impact

Rispondi con JSON strutturato per anno. Testo:
{text} 
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000
    )
    try:
        return json.loads(response.choices[0].message.content.strip())
    except:
        return {}

def calculate_kpi(df):
    df_out = df.copy()
    try: df_out['ROE (%)'] = (df['Net Income'] / df['Equity']) * 100
    except: pass
    try: df_out['ROI (%)'] = (df['Net Income'] / df['Total Assets']) * 100
    except: pass
    try: df_out['Net Margin (%)'] = (df['Net Income'] / df['Total Revenue']) * 100
    except: pass
    try: df_out['Debt to Equity'] = df['Total Debts'] / df['Equity']
    except: pass
    try: df_out['Assets to Equity'] = df['Total Assets'] / df['Equity']
    except: pass
    try: df_out['Cost to Revenue Ratio'] = df['Operating Costs'] / df['Total Revenue']
    except: pass
    try: df_out['EBITDA Margin (%)'] = (df['EBITDA'] / df['Total Revenue']) * 100
    except: pass
    try: df_out['Cash Flow to Debt'] = df['Cash Flow'] / df['Total Debts']
    except: pass
    try: df_out['Return on Debt (%)'] = (df['Net Income'] / df['Total Debts']) * 100
    except: pass
    try: df_out['Equity Multiplier'] = df['Total Assets'] / df['Equity']
    except: pass
    # KPI inventati per l'audit
    try: df_out['Indice Severità NC'] = (df['Total Debts'] + df['Operating Costs']) / df['Equity']
    except: pass
    try: df_out['Costo stimato NC (%)'] = (df['Operating Costs'] / df['Net Income']) * 100
    except: pass
    try: df_out['Indice Cultura Conformità'] = (df['Training Completed (%)'] / 100) * (1 - df['Recidiva NC (%)']/100)
    except: pass
    try: df_out['Audit Efficiency (giorni)'] = df['Audit Duration (days)']
    except: pass
    try: df_out['Indice Rischio Composito'] = df['Risk Probability'] * df['Risk Impact']
    except: pass
    return df_out

def show_dashboard(df):
    st.subheader("📊 Dashboard KPI Interattiva")
    for col in df.columns:
        if df[col].dtype in ['float64', 'int64'] and df[col].notna().all():
            fig = px.line(df, x=df.index, y=col, markers=True, title=col)
            st.plotly_chart(fig, use_container_width=True)

def generate_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Audit Flow Pro+ Report", ln=True)
    for year, row in df.iterrows():
        pdf.multi_cell(0, 10, f"{year}: {row.to_dict()}")
    output = "/mnt/data/auditflow_kpi_report.pdf"
    pdf.output(output)
    return output

if uploaded_file and api_key:
    file_name = uploaded_file.name
    if file_name.endswith(".pdf"):
        text = extract_text(uploaded_file.read())
        lang = detect_language(text)
        st.write(f"📘 Lingua rilevata: {'Italiano' if lang == 'it' else 'English'}")
        st.text_area("📄 Testo Estratto", text, height=300)
        data = extract_data_with_gpt(text, lang, api_key)
        df = pd.DataFrame(data).T if isinstance(data, dict) else pd.DataFrame()
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
        st.subheader("📈 KPI calcolati (finanziari + audit)")
        st.dataframe(df)

        show_dashboard(df)

        pdf_path = generate_pdf(df)
        with open(pdf_path, "rb") as f:
            st.download_button("📥 Scarica il report PDF", f, file_name="auditflow_kpi_report.pdf")
else:
    st.info("Carica un file e inserisci la tua API key OpenAI per iniziare.")
