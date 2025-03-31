import streamlit as st
import pandas as pd
import plotly.express as px
from utils import extract_text_from_file, detect_language, preprocess_text, extract_financial_data, calculate_kpis, generate_kpi_charts, generate_recommendations
from model import load_model, score_financial_sections

st.set_page_config(page_title="Audit Flow Pro+", layout="wide", page_icon="📊", initial_sidebar_state="expanded")
st.image("logo_auditflow.png", width=250)
st.title("Audit Flow Pro+")
st.markdown("### Analisi intelligente di bilanci aziendali con AI, Machine Learning e KPI")

uploaded_file = st.file_uploader("📁 Carica un bilancio aziendale (PDF, Excel, CSV)", type=["pdf", "xlsx", "xls", "csv"])
use_gpt = st.checkbox("💬 Attiva GPT (facoltativo)", value=False)
api_key = st.text_input("🔑 Inserisci API key OpenAI", type="password") if use_gpt else None

if uploaded_file:
    with st.spinner("📄 Estrazione e analisi in corso..."):
        raw_text = extract_text_from_file(uploaded_file)
        lang = detect_language(raw_text)
        st.markdown(f"🌐 **Lingua rilevata:** `{lang}`")
        cleaned_text = preprocess_text(raw_text, lang)
        model = load_model()
        relevant_text = score_financial_sections(cleaned_text, model)
        data = extract_financial_data(relevant_text)
        
        if not data:
            st.warning("⚠️ Nessun dato utile rilevato.")
        else:
            st.subheader("📊 Dati estratti")
            st.json(data)

            df_kpi = calculate_kpis(data)
            if not df_kpi.empty:
                st.subheader("📈 KPI calcolati")
                st.dataframe(df_kpi)
                generate_kpi_charts(df_kpi)
                st.subheader("📌 Raccomandazioni")
                recs = generate_recommendations(df_kpi, lang, use_gpt, api_key)
                st.markdown(recs)
            else:
                st.warning("⚠️ Nessun KPI calcolabile.")