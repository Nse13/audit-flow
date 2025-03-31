import streamlit as st
import pandas as pd
import plotly.express as px
from utils import extract_text_from_pdf, extract_key_values, calculate_kpi, generate_recommendations
from model import predict_relevance

st.set_page_config(page_title="AuditFlow ML Expert", layout="wide")

st.title("📊 AuditFlow ML Expert")
st.markdown("Versione intelligente con Machine Learning per analisi di bilanci aziendali PDF ed Excel.")

uploaded_file = st.file_uploader("📎 Carica un bilancio (PDF, XLSX o CSV)", type=["pdf", "xlsx", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith(".pdf"):
        text_pages = extract_text_from_pdf(uploaded_file)
        extracted = extract_key_values(text_pages)

        # Filtro intelligente basato su ML
        filtered = [item for item in extracted if predict_relevance(item["context"], item["value"])]

        if filtered:
            df_data = {item["label"]: item["value"] for item in filtered}
            st.json(df_data)

            df = pd.DataFrame([df_data])
            kpi = calculate_kpi(df_data)
            st.subheader("📈 KPI Calcolati")
            st.dataframe(pd.DataFrame([kpi]))

            chart_data = pd.DataFrame([kpi]).T.reset_index()
            chart_data.columns = ["KPI", "Valore"]
            fig = px.bar(chart_data, x="Valore", y="KPI", orientation="h")
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("💡 Raccomandazioni")
            for rec in generate_recommendations(kpi):
                st.markdown(f"- {rec}")
        else:
            st.warning("⚠️ Nessun dato rilevato come rilevante.")
    else:
        st.info("✅ Caricamento supportato, ma solo i PDF hanno analisi semantica con ML.")