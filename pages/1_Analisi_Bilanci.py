import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import extract_financial_data, calculate_kpis, plot_kpis

st.set_page_config(page_title="📊 Analisi Bilanci", layout="wide")
st.title("📊 Analisi Bilanci")
st.write("Carica un bilancio PDF o Excel per analisi automatica.")

# ✅ Caricamento file con estensione corretta
uploaded_file = st.file_uploader("📁 Carica un bilancio", type=["pdf", "xlsx", "xls"])

if uploaded_file:
    file_type = uploaded_file.name.split(".")[-1].lower()
    extension = f".{file_type}" if file_type in ["pdf", "xlsx", "xls"] else ""

    temp_file_path = f"temp_uploaded_file{extension}"

    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file.read())

    with st.spinner("Estrazione in corso..."):
        data, debug_info = extract_financial_data(temp_file_path, return_debug=True)

    st.subheader("📄 Dati estratti")
    st.json(data)

    if debug_info:
        with st.expander("🔍 Debug (dati grezzi estratti)"):
            st.write(debug_info)

    if data:
        st.subheader("📈 KPI Calcolati")
        kpis = calculate_kpis(data)
        st.dataframe(kpis)

        st.subheader("📊 Grafico KPI")
        fig = plot_kpis(kpis)
        st.plotly_chart(fig, use_container_width=True)
