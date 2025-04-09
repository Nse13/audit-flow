import streamlit as st
import os
import sys
sys.path.append("..")

from utils import (
    extract_financial_data,
    calculate_kpis,
    plot_kpis,
    salva_valore_confermato,
    generate_pdf_report,
    genera_commento_ai
)


st.title("📊 Analisi Bilanci Avanzata")

uploaded_file = st.file_uploader("Carica bilancio PDF, Excel, TXT o CSV", type=["pdf", "xlsx", "xls", "txt", "csv"])
use_debug = st.checkbox("📌 Mostra debug")
use_llm = st.checkbox("🤖 Usa AuditLLM (se attivo)")

if uploaded_file:
    file_path = "temp_uploaded_file"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())

    data, debug = extract_financial_data(file_path, return_debug=True)

    st.subheader("📄 Dati estratti automaticamente")
    st.json(data)

    st.subheader("✏️ Correggi manualmente i valori:")
    updated_data = {}
    for k, v in data.items():
        new_val = st.text_input(f"{k}:", value=str(v))
        try:
            updated_data[k] = float(new_val)
            if new_val != str(v):
                salva_valore_confermato(k, f"{k}: {new_val}", new_val)
        except:
            st.warning(f"⚠️ Valore non valido per {k}")

    st.subheader("📈 KPI Calcolati")
    df_kpis = calculate_kpis(updated_data)
    st.dataframe(df_kpis)
    st.plotly_chart(plot_kpis(df_kpis))

    # 🧠 Commento AI
    commento = ""
    if use_llm:
        with st.spinner("Generazione commento AI in corso..."):
            commento = genera_commento_ai(updated_data)
            st.subheader("🧠 Commento AuditLLM")
            st.write(commento)

    # 📥 Esporta PDF
    if st.button("📤 Scarica report PDF"):
        generate_pdf_report(updated_data, df_kpis, commento)
        with open("report_auditflow.pdf", "rb") as f:
            st.download_button("⬇️ Clicca per scaricare il PDF", f, file_name="report_auditflow.pdf")

    # 🔧 Simulatore
    if st.checkbox("🧪 Simula 'What if...'"):
        st.subheader("🔧 Simulazione KPI con valori ipotetici")
        dati_sim = {}
        for k, v in updated_data.items():
            simulato = st.number_input(f"{k} simulato:", value=v)
            dati_sim[k] = simulato
        st.dataframe(calculate_kpis(dati_sim))
        st.plotly_chart(plot_kpis(calculate_kpis(dati_sim)))

    # 🔁 Confronto Multi-file
    if st.checkbox("📂 Confronta più bilanci"):
        uploaded_files = st.file_uploader("Carica più bilanci", type=["pdf", "xlsx"], accept_multiple_files=True)
        dati_annuali = {}
        for f in uploaded_files:
            nome = f.name.split(".")[0]
            with open("temp_multi", "wb") as tmp:
                tmp.write(f.read())
            dati, _ = extract_financial_data("temp_multi", return_debug=False)
            dati_annuali[nome] = dati

        if dati_annuali:
            df_confronto = confronta_anni(dati_annuali)
            st.subheader("📊 Confronto KPI tra anni / aziende")
            st.dataframe(df_confronto)

    # 🔍 Debug
    if use_debug:
        st.subheader("🔍 Debug - Testo grezzo estratto")
        st.json(debug)
