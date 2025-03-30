
import streamlit as st
import fitz
import io
import re
import json
import pandas as pd
import plotly.express as px
from fpdf import FPDF
from PIL import Image
import pytesseract

try:
    from openai import OpenAI
    openai_available = True
except ImportError:
    openai_available = False

st.set_page_config(page_title="Audit Flow Hybrid - KPI Enhanced", layout="wide")
st.title("Audit Flow Pro+ Hybrid")
st.subheader("PDF, Excel, CSV + KPI, grafici, GPT fallback intelligente")

uploaded_file = st.sidebar.file_uploader("📂 Carica un bilancio (PDF, Excel, CSV)", type=["pdf", "xlsx", "xls", "csv"])
use_gpt = st.sidebar.toggle("🤖 Attiva GPT fallback", value=True)
api_key = st.sidebar.text_input("🔐 API key OpenAI", type="password") if use_gpt else None

def extract_text_from_pdf(pdf_bytes):
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

def parse_local(text):
    keywords = {
        "Revenue": ["ricavi", "revenues"],
        "Net Income": ["utile netto", "net income"],
        "Total Assets": ["attività totali", "total assets"],
        "Equity": ["patrimonio netto", "equity"],
        "Total Debts": ["debiti", "total debts", "liabilities"],
        "EBITDA": ["ebitda"],
        "Operating Costs": ["costi operativi", "operating costs"],
        "Cash Flow": ["cash flow", "flusso di cassa"]
    }

    results = {}
    for label, terms in keywords.items():
        for term in terms:
            pattern = rf"{term}[^\d-]*(\d+[.,\d]*)\s*(milioni|miliardi|mln|bn)?"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).replace(".", "").replace(",", ".")
                multiplier = 1
                unit = match.group(2)
                if unit:
                    if "miliard" in unit or "bn" in unit:
                        multiplier = 1_000_000_000
                    elif "milion" in unit or "mln" in unit:
                        multiplier = 1_000_000
                try:
                    num = float(value)
                    if num > 0:
                        results[label] = round(num * multiplier)
                except:
                    continue
                break
    return results

def gpt_fill(text, data, api_key):
    missing = [k for k in [
        "Revenue", "Net Income", "Total Assets", "Equity",
        "Total Debts", "EBITDA", "Operating Costs", "Cash Flow"
    ] if k not in data or data[k] == 0]
    if not missing:
        return data

    prompt = f"""Dal testo seguente, trova SOLO i seguenti dati di bilancio mancanti o nulli: {missing}.
Rispondi in JSON. Se i numeri sono in milioni/miliardi, convertili in euro.
Testo completo:
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
        extracted = json.loads(response.choices[0].message.content.strip())
        data.update({k: v for k, v in extracted.items() if v})
    except Exception as e:
        st.warning(f"GPT fallback error: {e}")
    return data

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
    pdf.cell(0, 10, "Audit Flow Hybrid Report", ln=True)
    pdf.cell(0, 10, "Dati:", ln=True)
    for k, v in data.items():
        pdf.cell(0, 10, f"{k}: {v}", ln=True)
    pdf.cell(0, 10, "KPI:", ln=True)
    for k, v in kpi.items():
        pdf.cell(0, 10, f"{k}: {v}", ln=True)
    output = "auditflow_hybrid_report.pdf"
    pdf.output(output)
    return output

if uploaded_file:
    file_type = uploaded_file.name.split(".")[-1].lower()
    text = ""

    if file_type == "pdf":
        try:
            text = extract_text_from_pdf(uploaded_file.read())
        except:
            st.error("Errore nel caricamento del PDF. Assicurati che il file sia valido.")
            st.stop()
    elif file_type in ["xlsx", "xls"]:
        df = pd.read_excel(uploaded_file)
        st.subheader("📊 Dati da Excel")
        st.dataframe(df)
        text = df.to_string()
    elif file_type == "csv":
        df = pd.read_csv(uploaded_file)
        st.subheader("📊 Dati da CSV")
        st.dataframe(df)
        text = df.to_string()
    else:
        st.error("Formato non supportato.")
        st.stop()

    st.text_area("📄 Testo estratto", text[:2000], height=300)

    data = parse_local(text)
    if use_gpt and api_key:
        data = gpt_fill(text, data, api_key)

    for key in data:
        try:
            data[key] = float(data[key])
        except:
            pass

    if data:
        st.subheader("📑 Dati estratti")
        st.json(data)

        kpi = calculate_kpi(data)
        st.subheader("📈 KPI calcolati")
        st.json(kpi)

        df_chart = pd.DataFrame.from_dict({**data, **kpi}, orient="index", columns=["Valore"])
        df_chart.reset_index(inplace=True)
        df_chart.rename(columns={"index": "KPI"}, inplace=True)
        fig = px.bar(df_chart, x="KPI", y="Valore", title="📊 Indicatori e KPI")
        st.plotly_chart(fig, use_container_width=True)

        pdf_path = generate_pdf(data, kpi)
        with open(pdf_path, "rb") as f:
            st.download_button("📥 Scarica il report PDF", f, file_name="auditflow_hybrid_report.pdf")
    else:
        st.warning("⚠️ Nessun dato rilevato.")
else:
    st.info("Carica un file per iniziare.")
