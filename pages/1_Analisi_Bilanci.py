import streamlit as st
import sys
import os
import tempfile

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import extract_financial_data, calculate_kpis, plot_kpis

st.title("📊 Analisi Bilanci")
st.write("Carica un file PDF, Excel o TXT per analisi automatica.")

uploaded_file = st.file_uploader("📁 Carica un bilancio", type=["pdf", "xlsx", "xls", "txt"])

if uploaded_file:
    suffix = "." + uploaded_file.name.split(".")[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        file_path = tmp.name

    with st.spinner("Estrazione e analisi in corso..."):
        data, debug_info = extract_financial_data(file_path, return_debug=True)

    st.subheader("📄 Dati estratti")
    st.json(data)

    st.subheader("📈 KPI Calcolati")
    kpis = calculate_kpis(data)
    st.dataframe(kpis)

    st.subheader("📊 Grafico KPI")
    fig = plot_kpis(kpis)
    st.plotly_chart(fig)

    with st.expander("🔍 Debug Estrazione"):
        st.write(debug_info)
