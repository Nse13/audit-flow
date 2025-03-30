
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

st.set_page_config(page_title="Audit Flow Pro GPT+ Guided", layout="wide")
st.title("Audit Flow Pro+ GPT Guided")
st.subheader("Parsing avanzato con riconoscimento unità e GPT mirato")

uploaded_file = st.sidebar.file_uploader("📂 Carica un bilancio", type=["pdf"])
use_gpt = st.sidebar.toggle("🤖 Attiva GPT fallback mirato", value=True)
api_key = st.sidebar.text_input("🔐 API key OpenAI", type="password") if use_gpt else None

def extract_text_with_ocr(pdf_bytes):
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

def parse_number_with_unit(value_str):
    value_str = value_str.lower()
    multiplier = 1
    if "miliard" in value_str or "billion" in value_str or "bn" in value_str:
        multiplier = 1_000_000_000
    elif "milion" in value_str or "million" in value_str or "mln" in value_str:
        multiplier = 1_000_000
    value = re.findall(r"[\d.,]+", value_str)
    if value:
        num = float(value[0].replace(".", "").replace(",", "."))
        return round(num * multiplier)
    return None

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
                        match = re.search(rf"{variant}.*?(\d+[.,\d\s]*\s*(milion|mln|miliard|bn|billion)?\s*euro?)", lower)
                        if match and label not in results:
                            try:
                                num = parse_number_with_unit(match.group(1))
                                if num and num > 1000:
                                    results[label] = num
                                    learned_patterns[label].append(variant)
                            except:
                                continue
    return pd.DataFrame([results], index=["2023"]) if results else pd.DataFrame()

def gpt_fill_missing(text, df, api_key):
    missing = [k for k in [
        "Revenue", "Net Income", "Total Assets", "Equity", "Total Debts",
        "EBITDA", "Operating Costs", "Cash Flow"
    ] if k not in df.columns]

    if not missing:
        return df

    prompt = f"""Dal testo seguente, trova SOLO i seguenti dati di bilancio mancanti: {missing}. 
Se sono scritti in milioni/miliardi, convertili in euro. 
Rispondi solo in JSON con i nomi esatti. 
Testo completo:
{text[:6000]}
"""

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=800
        )
        fixed = eval(response.choices[0].message.content.strip())
        for k, v in fixed.items():
            df[k] = v
    except Exception as e:
        st.warning(f"GPT fallback error: {e}")
    return df

def calculate_kpi(df):
    df_out = df.copy()
    try: df_out["ROE (%)"] = (df["Net Income"] / df["Equity"]) * 100
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
    pdf.cell(0, 10, "Audit Flow Pro+ Guided Report", ln=True)
    for year, row in df.iterrows():
        pdf.multi_cell(0, 10, f"{year}: {row.to_dict()}")
    output = "auditflow_guided_gpt_report.pdf"
    pdf.output(output)
    return output

if uploaded_file:
    pages = extract_text_with_ocr(uploaded_file.read())
    full_text = " ".join(pages.values())
    st.text_area("📄 Testo Estratto", full_text[:2000], height=300)

    df = learn_and_parse(pages)

    if use_gpt and api_key:
        df = gpt_fill_missing(full_text, df, api_key)

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
            st.download_button("📥 Scarica il report PDF", f, file_name="auditflow_guided_gpt_report.pdf")
    else:
        st.warning("⚠️ Nessun dato rilevato.")
else:
    st.info("Carica un PDF per iniziare.")
