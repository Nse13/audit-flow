import streamlit as st
from utils import extract_financial_data, calculate_kpis, plot_kpis, generate_recommendations
import gestionale

st.set_page_config(page_title="Audit Flow Pro+", layout="wide")
st.title("📊 Audit Flow Pro+")
st.subheader("Analisi e Audit intelligente dei bilanci aziendali")

uploaded_file = st.file_uploader("Carica bilancio (PDF, Excel, CSV)", type=["pdf", "xlsx", "xls", "csv"])
api_key = st.sidebar.text_input("🔑 OpenAI API Key (opzionale)", type="password")

if uploaded_file:
    data = extract_financial_data(uploaded_file)
    st.subheader("📄 Dati Estratti")
    st.json(data)

    kpis = calculate_kpis(data)
    st.subheader("📈 KPI")
    st.dataframe(kpis)

    st.subheader("📊 Grafici KPI")
    plot_kpis(kpis)

    st.subheader("💡 Raccomandazioni")
    recs = generate_recommendations(data, api_key=api_key)
    for rec in recs:
        st.info(rec)

    # Modulo Gestionale
    st.subheader("📚 Modulo Gestionale")
    gestionale.dashboard_contabile(data)