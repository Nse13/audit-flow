# --- main.py ---

import streamlit as st
import tempfile
import os
from utils import extract_financial_data, calculate_kpis, plot_kpis, generate_pdf_report, genera_commento_ai

st.set_page_config(page_title="Audit Flow+", layout="wide")
st.title("📊 Audit Flow+ - Analisi Automatica del Bilancio")

uploaded_file = st.file_uploader("📁 Carica un bilancio (PDF, Excel, Word, testo)", type=["pdf", "xlsx", "xls", "csv", "txt", "docx"])

if uploaded_file is not None:
    # Ricava estensione vera
    file_ext = os.path.splitext(uploaded_file.name)[1]

    # Salva file temporaneo con estensione corretta
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
        tmp_file.write(uploaded_file.read())
        temp_file_path = tmp_file.name

    st.subheader("🔎 Debug - Testo grezzo estratto")
    try:
        data, debug = extract_financial_data(temp_file_path, return_debug=True)
        st.json(debug)

        st.subheader("📄 Dati estratti automaticamente")
        st.json(data)

        st.subheader("🛠️ Correggi manualmente i valori (opzionale)")
        for k in data:
            new_val = st.text_input(f"{k}", value=str(data[k]))
            try:
                data[k] = float(new_val.replace(",", "."))
            except:
                pass

        st.subheader("📈 KPI Calcolati")
        df_kpis = calculate_kpis(data)
        st.dataframe(df_kpis)

        fig1, fig2 = plot_kpis(df_kpis)
        st.plotly_chart(fig1, use_container_width=True)
        st.plotly_chart(fig2, use_container_width=True)

        commento = ""
        if st.checkbox("🤖 Genera commento AI con AuditLLM (GPT)"):
            commento = genera_commento_ai(data)
            st.text_area("📝 Commento generato", commento, height=250)

        if st.button("📥 Scarica report PDF"):
            generate_pdf_report(data, df_kpis, commento)
            with open("report_auditflow.pdf", "rb") as f:
                st.download_button("📄 Download Report", f, file_name="report_auditflow.pdf")

    except Exception as e:
        st.error(f"Errore durante l'elaborazione del file: {str(e)}")
