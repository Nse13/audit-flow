# --- main.py ---

import streamlit as st
import tempfile
import os

from utils import (
    extract_financial_data,
    calculate_kpis,
    plot_kpis,
    generate_pdf_report,
    genera_commento_ai
)

# Impostazioni pagina
st.set_page_config(page_title="Audit Flow+", layout="wide")
st.title("📊 Audit Flow+ - Analisi Automatica del Bilancio")

# Caricamento file
uploaded_file = st.file_uploader(
    "📁 Carica un bilancio (PDF, Excel, Word, testo)",
    type=["pdf", "xlsx", "xls", "csv", "txt", "docx"]
)

if uploaded_file is not None:
    # 1) Salvo su file temporaneo con estensione corretta
    file_ext = os.path.splitext(uploaded_file.name)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
        tmp_file.write(uploaded_file.read())
        temp_file_path = tmp_file.name

    try:
        # 2) Estrazione dati + debug
        data, debug = extract_financial_data(temp_file_path, return_debug=True)
        st.subheader("🔎 Debug - Testo grezzo estratto")
        st.json(debug)

        # 3) Mostro dati estratti
        st.subheader("📄 Dati estratti automaticamente")
        st.json(data)

        # 4) Correzione manuale (opzionale)
        st.subheader("🛠️ Correggi manualmente i valori (opzionale)")
        for k in data:
            new_val = st.text_input(k, value=str(data[k]))
            try:
                data[k] = float(new_val.replace(",", "."))
            except ValueError:
                pass

        # 5) Calcolo KPI e li visualizzo
        st.subheader("📈 KPI Calcolati")
        df_kpis = calculate_kpis(data)
        st.dataframe(df_kpis)

        # 6) Grafici KPI (percentuali vs assoluti)
        fig1, fig2 = plot_kpis(df_kpis)
        st.plotly_chart(fig1, use_container_width=True)
        st.plotly_chart(fig2, use_container_width=True)

        # 7) Generazione commento AI (opzionale)
        if st.checkbox("🤖 Genera commento AI con AuditLLM (GPT)"):
            commento = genera_commento_ai(data)
            st.subheader("📝 Commento generato")
            st.text_area("", commento, height=200)

        # 8) Scarica report PDF
        if st.button("📥 Scarica report PDF"):
            # Se non hai creato 'commento' perché non hai cliccato la checkbox,
            # lo valorizziamo a stringa vuota:
            report_comment = commento if 'commento' in locals() else ""
            generate_pdf_report(data, df_kpis, report_comment)
            with open("report_auditflow.pdf", "rb") as f:
                st.download_button("📄 Download Report", f, file_name="report_auditflow.pdf")

    except Exception as e:
        st.error(f"Errore durante l'elaborazione del file: {e}")

else:
    st.info("📁 Carica un bilancio per iniziare l'analisi.")
