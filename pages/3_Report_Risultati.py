import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import extract_financial_data, calculate_kpis, generate_pdf_report, generate_gpt_comment

st.title("📈 Report & KPI")

uploaded_file = st.file_uploader("📁 Carica di nuovo il bilancio per generare il report", type=["pdf", "xlsx", "xls", "txt"])

if uploaded_file:
    suffix = "." + uploaded_file.name.split(".")[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        file_path = tmp.name

    with st.spinner("Estrazione in corso..."):
        data, _ = extract_financial_data(file_path)
        kpis_df = calculate_kpis(data)

    st.subheader("📊 KPI Calcolati")
    st.dataframe(kpis_df)

    commento = ""
    if st.checkbox("🧠 Genera commento GPT (opzionale)"):
        commento = generate_gpt_comment(data)
        st.subheader("💬 Commento GPT")
        st.write(commento)

    if st.button("📄 Genera Report PDF"):
        generate_pdf_report(data, kpis_df, commento)
        st.success("✅ Report generato: report_auditflow.pdf")
        with open("report_auditflow.pdf", "rb") as pdf_file:
            st.download_button(label="📥 Scarica il report", data=pdf_file, file_name="report_auditflow.pdf", mime="application/pdf")
from analisi_llm import genera_commento_llm

# Dopo avere già calcolato data e kpi_df
commento = genera_commento_llm(data, kpi_df)

st.subheader("🧠 Analisi AI (AuditLLM)")
st.write(commento)
