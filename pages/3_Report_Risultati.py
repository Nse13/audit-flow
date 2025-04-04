import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import extract_financial_data, calculate_kpis, generate_pdf_report, generate_gpt_comment

st.title("📈 Report & KPI")

uploaded_file = st.file_uploader("📁 Carica di nuovo il bilancio per generare il report", type=["pdf", "xlsx"])

if uploaded_file:
    with open("temp_report_file", "wb") as f:
        f.write(uploaded_file.read())

    with st.spinner("Estrazione in corso..."):
        data, _ = extract_financial_data("temp_report_file")
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
