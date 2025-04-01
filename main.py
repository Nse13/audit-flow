import streamlit as st
from utils import extract_financial_data, calculate_kpis, plot_kpis

st.set_page_config(page_title="Audit Flow Pro+", layout="wide")
st.title("📊 Audit Flow Pro+")
st.subheader("Estrazione e analisi automatica da bilanci PDF/Excel")

uploaded_file = st.file_uploader("Carica un file", type=["pdf", "txt"])
if uploaded_file:
    with open("temp_uploaded_file", "wb") as f:
        f.write(uploaded_file.read())
    
    with st.spinner("Estrazione in corso..."):
        data, debug_info = extract_financial_data("temp_uploaded_file", return_debug=True)

    st.subheader("📄 Dati estratti")
    st.json(data)

    if debug_info:
        with st.expander("🔍 Debug - Fonte dei dati estratti"):
            st.write(debug_info)

    if data:
        kpis = calculate_kpis(data)
        st.subheader("📈 KPI Calcolati")
        st.dataframe(kpis)
        st.subheader("📊 Visualizzazione KPI")
        plot_kpis(kpis)