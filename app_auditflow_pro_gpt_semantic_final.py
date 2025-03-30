
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

st.set_page_config(page_title="Audit Flow Pro+ Semantic", layout="wide", initial_sidebar_state="expanded")
st.image("logo_auditflow.png", width=300)
st.title("Audit Flow Pro+")
st.subheader("Analisi intelligente e verificabile di bilanci PDF/Excel/CSV")

uploaded_file = st.sidebar.file_uploader("📂 Carica un bilancio", type=["pdf", "xlsx", "xls", "csv"])
use_gpt = st.sidebar.toggle("🤖 Usa GPT per l'analisi", value=False)
api_key = st.sidebar.text_input("🔐 API key OpenAI", type="password") if use_gpt else None

def extract_text_with_pages(pdf_bytes):
    pages = {}
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for i, page in enumerate(doc):
            pages[i+1] = page.get_text()
    return pages

def detect_language(text):
    try:
        return "it" if langdetect.detect(text) == "it" else "en"
    except:
        return "en"

def parse_semantic(text_dict):
    keywords = {
        "Revenue": ["net revenues", "ricavi", "sales", "revenues"],
        "Net Income": ["net income", "utile netto", "profit for the year"],
        "Total Assets": ["total assets", "attività totali"],
        "Equity": ["total equity", "patrimonio netto"],
        "EBITDA": ["ebitda"],
        "Cash Flow": ["cash flow", "flusso di cassa"],
        "Operating Costs": ["operating expenses", "costi operativi"],
        "Total Debts": ["total liabilities", "debiti totali"]
    }

    results = {}
    for page, text in text_dict.items():
        lower = text.lower()
        for label, variants in keywords.items():
            for variant in variants:
                pattern = rf"{variant}[^\d]*(\d{{1,3}}(?:[.,]\d{{3}})*(?:[.,]\d{{2}})?)"
                match = re.search(pattern, lower)
                if match and label not in results:
                    number = match.group(1).replace(".", "").replace(",", "")
                    try:
                        results[label] = float(number)
                        results[f"{label}_page"] = page
                    except:
                        continue
    return pd.DataFrame([results], index=["2023"]) if results else pd.DataFrame()

def extract_data_with_gpt(text, lang, api_key):
    try:
        client = OpenAI(api_key=api_key)
        prompt = f"""Estrai in formato JSON i principali dati di bilancio da questo testo:
{text[:5000]}"""
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000
        )
        return pd.DataFrame(eval(response.choices[0].message.content.strip()), index=["GPT"])
    except Exception as e:
        st.warning(f"Errore GPT: {e}")
        return pd.DataFrame()

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
    st.subheader("📊 Dashboard KPI")
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
    path = "auditflow_report_semantic.pdf"
    pdf.output(path)
    return path

if uploaded_file:
    file_name = uploaded_file.name
    if file_name.endswith(".pdf"):
        pages = extract_text_with_pages(uploaded_file.read())
        all_text = " ".join(pages.values())
        lang = detect_language(all_text)
        st.write(f"📘 Lingua rilevata: {'Italiano' if lang == 'it' else 'English'}")
        st.text_area("📄 Testo Estratto (inizio)", all_text[:1500], height=300)

        df = extract_data_with_gpt(all_text, lang, api_key) if use_gpt and api_key and openai_available else parse_semantic(pages)

    elif file_name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    elif file_name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        st.stop()

    if not df.empty:
        df.index.name = "Source"
        st.subheader("📑 Dati Estratti")
        st.dataframe(df)

        df_kpi = calculate_kpi(df)
        st.subheader("📈 KPI Calcolati")
        st.dataframe(df_kpi)

        show_dashboard(df_kpi)

        pdf_path = generate_pdf(df_kpi)
        with open(pdf_path, "rb") as f:
            st.download_button("📥 Scarica il report PDF", f, file_name="auditflow_report_semantic.pdf")
    else:
        st.warning("⚠️ Nessun dato utile trovato.")
else:
    st.info("Carica un file per iniziare.")
