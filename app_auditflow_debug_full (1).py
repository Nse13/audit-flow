
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import pytesseract
from PIL import Image
import fitz
import io
import json
import os
from fpdf import FPDF
from app_auditflow_recommendation_engine import generate_recommendations

st.set_page_config(page_title="Audit Flow Pro+ (Debug)", page_icon="📊", layout="wide")

st.image("logo_auditflow.png", width=250)
st.title("Audit Flow Pro+ con Raccomandazioni Intelligenti (🛠️ Debug Mode)")

uploaded_file = st.file_uploader("📂 Carica un bilancio PDF, Excel o CSV", type=["pdf", "xlsx", "xls", "csv"])

use_gpt = st.checkbox("🧠 Usa GPT se disponibile (richiede API key)", value=False)
api_key = st.text_input("🔐 API key OpenAI (facoltativa)", type="password") if use_gpt else None

def extract_text_from_pdf(pdf_bytes):
    text = ""
    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
    except:
        st.error("❌ Errore durante la lettura del PDF.")
    return text

def perform_ocr(image_bytes):
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(image)
    except:
        return ""

def calculate_kpi(df):
    try:
        df["ROI"] = (df["Net Income"] / df["Total Assets"]) * 100
        df["ROE"] = (df["Net Income"] / df["Equity"]) * 100
        df["ROS"] = (df["Net Income"] / df["Revenue"]) * 100
        return df
    except:
        st.warning("⚠️ Impossibile calcolare KPI. Controlla i dati.")
        return pd.DataFrame()

def generate_pdf_report(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Audit Flow Pro+ Report", ln=True)
    for col in df.columns:
        pdf.cell(200, 10, txt=f"{col}: {df[col].values[0]}", ln=True)
    path = "/mnt/data/auditflow_debug_report.pdf"
    pdf.output(path)
    return path

if uploaded_file:
    with st.spinner("📄 Elaborazione file in corso..."):
        name = uploaded_file.name
        if name.endswith(".pdf"):
            text = extract_text_from_pdf(uploaded_file.read())
            st.subheader("📄 Testo Estratto")
            st.text(text[:1000] + "..." if len(text) > 1000 else text)
            st.warning("⚠️ Estrazione da PDF solo testuale. Controlla il risultato.")
        else:
            try:
                if name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                st.subheader("📊 Dati da Excel/CSV")
                st.dataframe(df)

                st.subheader("📈 KPI Calcolati")
                df_kpi = calculate_kpi(df)
                st.dataframe(df_kpi)

                pdf_path = generate_pdf_report(df_kpi)
                with open(pdf_path, "rb") as f:
                    st.download_button("📥 Scarica report PDF", f, file_name="report_auditflow_debug.pdf")

                st.subheader("🤖 Raccomandazioni")
                st.write(generate_recommendations(df_kpi))

            except Exception as e:
                st.error(f"❌ Errore durante l'elaborazione: {e}")
else:
    st.info("📁 Carica un file per iniziare.")
