
import streamlit as st
import pandas as pd
import fitz
import io
import re
import json
import langdetect
from fpdf import FPDF
import plotly.express as px
from collections import defaultdict
from PIL import Image
import pytesseract

try:
    from openai import OpenAI
    openai_available = True
except ImportError:
    openai_available = False

learned_patterns = defaultdict(list)
learned_data_path = "auditflow_memory.json"

try:
    with open(learned_data_path, "r") as f:
        learned_patterns.update(json.load(f))
except:
    pass

st.set_page_config(page_title="Audit Flow OCR+GPT", layout="wide")
st.image("logo_auditflow.png", width=300)
st.title("Audit Flow Pro+ OCR+GPT")
st.subheader("Supporto completo per PDF difficili, OCR e fallback GPT")

uploaded_file = st.sidebar.file_uploader("📂 Carica un bilancio", type=["pdf", "xlsx", "xls", "csv"])
use_gpt = st.sidebar.toggle("🤖 Usa GPT per fallback", value=True)
api_key = st.sidebar.text_input("🔐 API key OpenAI", type="password") if use_gpt else None

def extract_text_with_fallback(pdf_bytes):
    pages = {}
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for i, page in enumerate(doc):
            text = page.get_text()
            if not text.strip():
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                text = pytesseract.image_to_string(img)
            pages[i+1] = text
    return pages

def detect_language(text):
    try:
        return "it" if langdetect.detect(text) == "it" else "en"
    except:
        return "en"

def learn_and_parse(pages):
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
    for page, text in pages.items():
        lines = text.splitlines()
        for line in lines:
            lower = line.lower()
            for label, variants in keywords.items():
                known = learned_patterns[label] + variants
                for variant in known:
                    if variant in lower:
                        pattern = rf"{variant}\s*[:\-]?\s*(\d{{1,3}}(?:[.,]\d{{3}})*(?:[.,]\d{{2}})?)"
                        match = re.search(pattern, lower)
                        if match and label not in results:
                            try:
                                num = float(match.group(1).replace(".", "").replace(",", ""))
                                if num > 1000:
                                    results[label] = num
                                    learned_patterns[label].append(variant)
                            except:
                                continue
    return pd.DataFrame([results], index=["2023"]) if results else pd.DataFrame()

def validate_with_gpt(text, raw_df, api_key):
    try:
        client = OpenAI(api_key=api_key)
        prompt = f"""Controlla e correggi i dati rilevati:
{raw_df.to_dict()}
Testo: {text[:4000]}"""
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800
        )
        fixed = eval(response.choices[0].message.content.strip())
        return pd.DataFrame([fixed], index=["GPT Fallback"])
    except Exception as e:
        st.warning(f"GPT Fallback error: {e}")
        return raw_df

def calculate_kpi(df):
    df_out = df.copy()
    try: df_out["ROE (%)"] = (df["Net Income"] / df["Equity"]) * 100
    except: pass
    try: df_out["ROI (%)"] = (df["Net Income"] / df["Total Assets"]) * 100
    except: pass
    try: df_out["Net Margin (%)"] = (df["Net Income"] / df["Revenue"]) * 100
    except: pass
    try: df_out["Debt to Equity"] = df["Total Debts"] / df["Equity"]
    except: pass
    try: df_out["EBITDA Margin (%)"] = df["EBITDA"] / df["Revenue"] * 100
    except: pass
    return df_out

def generate_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Audit Flow OCR+GPT Report", ln=True)
    for year, row in df.iterrows():
        pdf.multi_cell(0, 10, f"{year}: {row.to_dict()}")
    output = "auditflow_ocr_gpt_report.pdf"
    pdf.output(output)
    return output

if uploaded_file:
    file_name = uploaded_file.name
    if file_name.endswith(".pdf"):
        pages = extract_text_with_fallback(uploaded_file.read())
        full_text = " ".join(pages.values())
        lang = detect_language(full_text)
        st.write(f"📘 Lingua rilevata: {'Italiano' if lang == 'it' else 'English'}")
        st.text_area("📄 Testo Estratto (inizio)", full_text[:1500], height=300)

        df = learn_and_parse(pages)
        if df.empty and use_gpt and api_key:
            df = validate_with_gpt(full_text, df, api_key)
    elif file_name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
    elif file_name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        st.stop()

    if not df.empty:
        df.index.name = "Fonte"
        st.subheader("📑 Dati rilevati")
        st.dataframe(df)

        df_kpi = calculate_kpi(df)
        st.subheader("📈 KPI calcolati")
        st.dataframe(df_kpi)

        fig = px.bar(df_kpi.T, title="📊 KPI principali")
        st.plotly_chart(fig, use_container_width=True)

        pdf_path = generate_pdf(df_kpi)
        with open(pdf_path, "rb") as f:
            st.download_button("📥 Scarica il report PDF", f, file_name="auditflow_ocr_gpt_report.pdf")

        with open(learned_data_path, "w") as f:
            json.dump(learned_patterns, f, indent=2)
    else:
        st.warning("⚠️ Nessun dato rilevato neanche dopo OCR e fallback GPT.")
else:
    st.info("Carica un file per iniziare.")
