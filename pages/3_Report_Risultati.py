import streamlit as st
from utils import extract_financial_data, calculate_kpis, plot_kpis
from analisi_llm import genera_commento_llm

st.set_page_config(page_title="📈 Report & KPI", layout="wide")
st.title("📈 Report & KPI")

uploaded_file = st.file_uploader("📁 Carica un bilancio (PDF o Excel)", type=["pdf", "xlsx", "xls"])
use_gpt = st.checkbox("Fallback GPT (solo se attivo)", value=False)

if uploaded_file:
    with open("temp_report_file", "wb") as f:
        f.write(uploaded_file.read())

    with st.spinner("Estrazione e analisi in corso..."):
        data, _ = extract_financial_data("temp_report_file", return_debug=True, use_gpt=use_gpt)
        kpi_df = calculate_kpis(data)

    st.subheader("📄 Dati Estratti")
    st.json(data)

    st.subheader("📊 KPI Calcolati")
    st.dataframe(kpi_df)
    st.plotly_chart(plot_kpis(kpi_df), use_container_width=True)

    st.subheader("🧠 Analisi AI - AuditLLM")
    if st.button("🔍 Genera Commento AI"):
        with st.spinner("AuditLLM sta analizzando..."):
            commento = genera_commento_llm(data, kpi_df)
        st.markdown("### 💬 Commento AuditLLM")
        st.write(commento)
