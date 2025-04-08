import streamlit as st
import os
import sys
sys.path.append("..")

from utils import extract_financial_data, calculate_kpis, plot_kpis, salva_valore_confermato

st.title("📊 Analisi Bilanci Avanzata")

uploaded_file = st.file_uploader("Carica bilancio PDF, Excel, TXT o CSV", type=["pdf", "xlsx", "xls", "txt", "csv"])
use_debug = st.checkbox("📌 Mostra debug")
use_llm = st.checkbox("🤖 Usa AuditLLM (se attivo)")

if uploaded_file:
    # Salva il file caricato
    file_path = "temp_uploaded_file"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())

    # Estrai dati
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

    # Calcolo KPI
    st.subheader("📈 KPI Calcolati")
    df_kpis = calculate_kpis(updated_data)
    st.dataframe(df_kpis)
    st.plotly_chart(plot_kpis(df_kpis))

    # Debug
    if use_debug:
        st.subheader("🔍 Debug - Testo grezzo estratto")
        st.json(debug)
