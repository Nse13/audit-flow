
import streamlit as st
import pandas as pd
import plotly.express as px
import fitz
import io
import re
from PIL import Image
import pytesseract
from fpdf import FPDF
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

try:
    from openai import OpenAI
    openai_available = True
except ImportError:
    openai_available = False

st.set_page_config(page_title="Audit Flow Pro+ ML", layout="wide")
st.title("📊 Audit Flow Pro+ con Machine Learning")
st.subheader("Analisi PDF, Excel, CSV + GPT + ML Clustering")

uploaded_file = st.sidebar.file_uploader("📂 Carica file PDF, Excel o CSV", type=["pdf", "xlsx", "xls", "csv"])
use_gpt = st.sidebar.toggle("🤖 Attiva fallback GPT", value=True)
api_key = st.sidebar.text_input("🔐 API key OpenAI", type="password") if use_gpt else None

# KPI calculator per singola riga
def calculate_kpi(row):
    kpi = {}
    try: kpi["ROE (%)"] = round(row["Net Income"] / row["Equity"] * 100, 2)
    except: pass
    try: kpi["Net Margin (%)"] = round(row["Net Income"] / row["Revenue"] * 100, 2)
    except: pass
    try: kpi["Debt to Equity"] = round(row["Total Debts"] / row["Equity"], 2)
    except: pass
    try: kpi["EBITDA Margin (%)"] = round(row["EBITDA"] / row["Revenue"] * 100, 2)
    except: pass
    return kpi

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

    prompt = f"""Dal testo seguente, trova SOLO i seguenti dati mancanti o nulli: {missing}.
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

def apply_ml_clustering(text):
    vectorizer = TfidfVectorizer(stop_words="english", max_features=100)
    X = vectorizer.fit_transform(text.split("\n"))
    kmeans = KMeans(n_clusters=2, n_init=10, random_state=42)
    labels = kmeans.fit_predict(X)

    clustered = {}
    for i, line in enumerate(text.split("\n")):
        label = labels[i]
        if label not in clustered:
            clustered[label] = []
        clustered[label].append(line.strip())

    return clustered

if uploaded_file:
    ext = uploaded_file.name.split(".")[-1].lower()

    if ext in ["xlsx", "xls"]:
        df = pd.read_excel(uploaded_file)
        st.subheader("📊 Dati da Excel")
        st.dataframe(df)

        if "Year" in df.columns:
            df_kpi = df.copy()
            kpi_results = []

            for _, row in df.iterrows():
                row_kpi = calculate_kpi(row)
                row_kpi["Year"] = row["Year"]
                kpi_results.append(row_kpi)

            kpi_df = pd.DataFrame(kpi_results).set_index("Year")
            st.subheader("📈 KPI Calcolati")
            st.dataframe(kpi_df)

            st.subheader("📉 Grafici KPI")
            for col in kpi_df.columns:
                fig = px.line(kpi_df, x=kpi_df.index, y=col, markers=True, title=col)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Aggiungi una colonna 'Year' per abilitare analisi multi-periodo.")

    elif ext == "csv":
        df = pd.read_csv(uploaded_file)
        st.subheader("📊 Dati da CSV")
        st.dataframe(df)

    elif ext == "pdf":
        text = extract_text_from_pdf(uploaded_file.read())
        st.subheader("📄 Testo estratto")
        st.text_area("Contenuto PDF", text[:3000], height=300)

        data = parse_local(text)
        if use_gpt and api_key:
            data = gpt_fill(text, data, api_key)

        clustered = apply_ml_clustering(text)
        st.subheader("🧠 Machine Learning - Clustering semantico")
        for cluster, lines in clustered.items():
            with st.expander(f"Cluster {cluster}"):
                for line in lines:
                    st.markdown(f"- {line}")

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
        else:
            st.warning("⚠️ Nessun dato rilevato.")
else:
    st.info("Carica un file per iniziare.")
