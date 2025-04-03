import streamlit as st
from utils import extract_financial_data, calculate_kpis, plot_kpis

st.title("📊 Analisi Bilanci")
st.write("Carica un bilancio PDF o Excel per analisi automatica.")

uploaded_file = st.file_uploader("📁 Carica un bilancio", type=["pdf", "xlsx"])

if uploaded_file:
    with open("temp_uploaded_file", "wb") as f:
        f.write(uploaded_file.read())

    with st.spinner("Estrazione e analisi in corso..."):
        data, debug_info = extract_financial_data("temp_uploaded_file", return_debug=True)

    st.subheader("📄 Dati estratti")
    st.json(data)

    st.subheader("📈 KPI Calcolati")
    kpis = calculate_kpis(data)
    st.dataframe(kpis)

    st.subheader("📊 Grafico KPI")
    fig = plot_kpis(kpis)
    st.plotly_chart(fig)

    if debug_info:
        with st.expander("🔍 Debug Estrazione"):
            st.write(debug_info)
