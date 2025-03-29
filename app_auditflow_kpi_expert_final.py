
import streamlit as st
import pandas as pd
import fitz
import io
import langdetect
from fpdf import FPDF
import openai
import json
import plotly.express as px

st.set_page_config(page_title="Audit Flow Pro+ Dashboard", layout="wide")
st.title("Audit Flow Pro+ Dashboard")
st.subheader("Analisi avanzata di bilanci PDF, Excel o CSV con GPT e dashboard interattiva")

uploaded_file = st.sidebar.file_uploader("📂 Carica un bilancio (PDF, Excel o CSV)", type=["pdf", "xlsx", "xls", "csv"])
api_key = st.sidebar.text_input("🔐 API key OpenAI", type="password")

# Estrai testo da PDF
def extract_text(pdf_bytes):
    text = ""
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

# Rileva lingua testo
def detect_language(text):
    try:
        lang = langdetect.detect(text)
        return "it" if lang == "it" else "en"
    except:
        return "en"

# Estrai dati finanziari con GPT
def extract_data_with_gpt(text, lang, api_key):
    openai.api_key = api_key
    prompt_it = f"""Analizza il seguente testo di bilancio e restituisci i valori principali in formato JSON per ciascun anno se presente:
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

Rispondi solo con il JSON strutturato per anno, senza spiegazioni."""

    prompt_en = f"""Analyze the following financial report and return the main financial values in structured JSON by year if present:
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

Respond with structured JSON only, no explanation."""

    prompt = prompt_it if lang == "it" else prompt_en

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000
    )

    try:
        raw = response.choices[0].message.content.strip()
        return json.loads(raw)
    except:
        return {}

# Calcola KPI

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
    # Nuovi KPI per l'audit
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

    kpi = pd.DataFrame()
    try:
        kpi["ROE (%)"] = (df["Net Income"] / df["Equity"]) * 100
        kpi["ROI (%)"] = (df["Net Income"] / df["Total Assets"]) * 100
        kpi["Net Margin (%)"] = (df["Net Income"] / df["Total Revenue"]) * 100
        df = pd.concat([df, kpi], axis=1)
    except:
        pass
    return df

# Mostra grafici KPI
def show_dashboard(df):
    st.subheader("📈 Dashboard Interattiva")
    for column in ["ROE (%)", "ROI (%)", "Net Margin (%)"]:
        if column in df.columns:
            fig = px.line(df, x=df.index, y=column, markers=True, title=column)
            st.plotly_chart(fig, use_container_width=True)

# PDF finale
def generate_pdf(df, lang):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Audit Flow Pro+ Report", ln=True)
    for year, row in df.iterrows():
        pdf.multi_cell(0, 10, f"{year}: {row.to_dict()}")
    output = "auditflow_dashboard_report.pdf"
    pdf.output(output)
    return output

# Main
if uploaded_file and api_key:
    file_name = uploaded_file.name
    if file_name.endswith(".pdf"):
        text = extract_text(uploaded_file.read())
        lang = detect_language(text)
        st.write(f"📘 Lingua rilevata: {'Italiano' if lang == 'it' else 'English'}")
        st.text_area("📄 Testo estratto", text, height=250)
        data = extract_data_with_gpt(text, lang, api_key)
        if isinstance(data, dict):
            df = pd.DataFrame(data).T
        else:
            st.warning("⚠️ GPT non ha restituito un JSON valido.")
            df = pd.DataFrame()

    elif file_name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    elif file_name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        st.stop()

    if not df.empty:
        df.index.name = "Year"
        st.subheader("📊 Dati estratti o caricati")
        st.dataframe(df)

        df = calculate_kpi(df)
        st.subheader("📈 KPI Calcolati")
        st.dataframe(df[["ROE (%)", "ROI (%)", "Net Margin (%)"]])

        show_dashboard(df)

        pdf_path = generate_pdf(df, lang if 'lang' in locals() else 'en')
        with open(pdf_path, "rb") as f:
            st.download_button("📥 Scarica il report PDF", f, file_name="auditflow_dashboard_report.pdf")
else:
    st.info("Carica un file PDF, Excel o CSV e inserisci la tua OpenAI API key.")
