import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import extract_financial_data, calculate_kpis, plot_kpis

st.set_page_config(page_title="📊 Analisi Bilanci", layout="wide")
st.title("📊 Analisi Bilanci")
st.write("Carica un bilancio PDF o Excel per analisi automatica.")

uploaded_file = st.file_uploader("📁 Carica un bilancio", type=["pdf", "xlsx", "xls"])
use_gpt = st.checkbox("Fallback GPT (solo se attivo)", value=False)

if uploaded_file:
    with open("temp_uploaded_file", "wb") as f:
        f.write(uploaded_file.read())

    with st.spinner("Estrazione e analisi in corso..."):
        data, debug_info = extract_financial_data("temp_uploaded_file", return_debug=True, use_gpt=use_gpt)

    st.subheader("📄 Dati estratti")
    st.json(data)

    st.subheader("📊 KPI Calcolati")
    kpis = calculate_kpis(data)
    st.dataframe(kpis)

    st.subheader("📈 Grafico KPI")
    st.plotly_chart(plot_kpis(kpis), use_container_width=True)

    if debug_info:
        with st.expander("🔍 Debug (dati grezzi estratti)"):
            st.write(debug_info)

