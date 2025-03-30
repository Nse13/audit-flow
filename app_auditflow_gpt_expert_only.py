
import streamlit as st
import fitz
import io
import langdetect
import json
from fpdf import FPDF
from PIL import Image
import pytesseract

try:
    from openai import OpenAI
    openai_available = True
except ImportError:
    openai_available = False

st.set_page_config(page_title="Audit Flow GPT Expert", layout="wide")
st.title("Audit Flow Pro+ GPT Expert Only")
st.subheader("Estrazione completa dei dati solo tramite GPT e analisi semantica avanzata")

uploaded_file = st.sidebar.file_uploader("📂 Carica un PDF del bilancio")
api_key = st.sidebar.text_input("🔐 API key OpenAI", type="password")

def extract_full_text(pdf_bytes):
    pages = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text = page.get_text()
            if not text.strip():
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                text = pytesseract.image_to_string(img)
            pages.append(text)
    return "\n".join(pages)

def gpt_extract(text, api_key):
    prompt = f"""Analizza questo testo e restituisci in JSON i seguenti dati:
- Revenue (in euro)
- Net Income
- Total Assets
- Equity
- Total Debts
- EBITDA
- Operating Costs
- Cash Flow

Se i valori sono scritti in milioni o miliardi, converti in euro. Non scrivere nulla oltre il JSON.
Testo:
{text[:12000]}
"""
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=800
        )
        raw_json = response.choices[0].message.content.strip()
        data = json.loads(raw_json)
        return data
    except Exception as e:
        st.error(f"Errore GPT: {e}")
        return None

def calculate_kpi(data):
    kpi = {}
    try: kpi["ROE (%)"] = round(data["Net Income"] / data["Equity"] * 100, 2)
    except: pass
    try: kpi["Net Margin (%)"] = round(data["Net Income"] / data["Revenue"] * 100, 2)
    except: pass
    try: kpi["Debt to Equity"] = round(data["Total Debts"] / data["Equity"], 2)
    except: pass
    try: kpi["EBITDA Margin (%)"] = round(data["EBITDA"] / data["Revenue"] * 100, 2)
    except: pass
    return kpi

def generate_pdf(data, kpi):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Audit Flow GPT Expert Report", ln=True)
    pdf.cell(0, 10, "Dati estratti:", ln=True)
    for k, v in data.items():
        pdf.cell(0, 10, f"{k}: {v}", ln=True)
    pdf.cell(0, 10, "KPI calcolati:", ln=True)
    for k, v in kpi.items():
        pdf.cell(0, 10, f"{k}: {v}", ln=True)
    output = "auditflow_gpt_expert_report.pdf"
    pdf.output(output)
    return output

if uploaded_file and api_key and openai_available:
    text = extract_full_text(uploaded_file.read())
    st.text_area("📄 Testo estratto", text[:2000], height=300)

    with st.spinner("🧠 Estrazione in corso..."):
        data = gpt_extract(text, api_key)

    if data:
        st.subheader("📑 Dati estratti con GPT")
        st.json(data)

        kpi = calculate_kpi(data)
        st.subheader("📊 KPI calcolati")
        st.json(kpi)

        pdf_path = generate_pdf(data, kpi)
        with open(pdf_path, "rb") as f:
            st.download_button("📥 Scarica il report PDF", f, file_name="auditflow_gpt_expert_report.pdf")
    else:
        st.warning("⚠️ Nessun dato estratto.")
else:
    st.info("Carica un PDF e inserisci la API key per iniziare.")
