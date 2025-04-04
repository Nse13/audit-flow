import streamlit as st
import tempfile
import os
from utils import extract_financial_data, calculate_kpis, plot_kpis

st.title("📊 Analisi Bilanci")
st.write("Carica un bilancio PDF per analisi automatica.")

uploaded_file = st.file_uploader("📁 Carica un bilancio", type=["pdf"])

use_gpt = st.checkbox("Utilizza GPT per l'analisi avanzata dei dati")

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        file_path = tmp.name

    with st.spinner("Estrazione e analisi in corso..."):
        result = extract_financial_data(file_path, use_gpt=use_gpt)

    if use_gpt:
        st.subheader("📄 Analisi GPT")
        st.write(result)
    else:
        st.subheader("📄 Dati estratti")
        st.json(result)

        st.subheader("📈 KPI Calcolati")
        kpis = calculate_kpis(result)
        st.dataframe(kpis)

        st.subheader("📊 Grafico KPI")
        fig = plot_kpis(kpis)
        st.plotly_chart(fig)

    os.remove(file_path)
