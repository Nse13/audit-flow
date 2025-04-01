import streamlit as st
from utils import extract_financial_data, generate_kpi_charts

st.set_page_config(page_title="Audit Flow Pro+", layout="wide")
st.title("📊 Audit Flow Pro+")
st.subheader("Estrazione e analisi automatica da bilanci PDF/Excel/JSON")

uploaded_file = st.file_uploader("Carica un file", type=["pdf", "txt", "json"])
if uploaded_file:
    try:
        bytes_data = uploaded_file.read()
        text = bytes_data.decode("utf-8", errors="ignore")
        data = extract_financial_data(text)
        
        st.subheader("📄 Dati estratti")
        st.json(data)

        if data and any(isinstance(v, (int, float)) and v != 0 for v in data.values()):
            st.subheader("📊 KPI Calcolati")
            fig = generate_kpi_charts(data)
            st.plotly_chart(fig)
        else:
            st.warning("⚠️ Nessun dato utile rilevato per i KPI.")

    except Exception as e:
        st.error(f"Errore durante l'elaborazione del file: {str(e)}")