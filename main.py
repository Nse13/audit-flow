import streamlit as st
import pandas as pd
import plotly.express as px
from utils import extract_text_from_file, detect_language, preprocess_text, extract_financial_data, calculate_kpis, generate_kpi_charts, generate_recommendations, analyze_trends

st.set_page_config(page_title="Audit Flow Pro+", page_icon="📊", layout="wide")
st.image("logo_auditflow.png", width=250)
st.title("Audit Flow Pro+")
st.markdown("""
Analisi automatica di bilanci PDF, Excel, CSV. Supporto multilingua, trend, KPI e raccomandazioni intelligenti.
""")

uploaded_file = st.file_uploader("Carica un bilancio PDF, Excel o CSV", type=["pdf", "xlsx", "xls", "csv"])

if uploaded_file:
    raw_text = extract_text_from_file(uploaded_file)
    language = detect_language(raw_text)
    clean_text = preprocess_text(raw_text)
    data = extract_financial_data(clean_text)

    st.subheader("📑 Dati estratti")
    st.json(data)

    if data is not None and not data.empty:
        kpis = calculate_kpis(data)
        st.subheader("📈 KPI Calcolati")
        st.dataframe(pd.DataFrame([kpis]))

        st.subheader("📊 Visualizzazione KPI")
        fig = generate_kpi_charts(kpis)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📉 Analisi Tendenze (se presenti più anni)")
        trends = analyze_trends(data)
        if not trends.empty:
            st.line_chart(trends.set_index("Year"))

        st.subheader("💡 Raccomandazioni")
        recommendations = generate_recommendations(data)
        for rec in recommendations:
            st.info(rec)
    else:
        st.warning("⚠️ Nessun dato rilevato.")
