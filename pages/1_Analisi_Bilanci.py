import streamlit as st
import os
import sys
import json

# 📌 Per importare utils.py dalla cartella principale
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import (
    extract_financial_data,
    calculate_kpis,
    plot_kpis,
    load_learned_patterns,
    save_learned_pattern,
    smart_extract_value
)

st.set_page_config(page_title="📊 Analisi Bilanci", layout="wide")
st.title("📊 Analisi Bilanci")
st.markdown("Carica un bilancio PDF o Excel per analisi automatica intelligente.")

# Upload del file
uploaded_file = st.file_uploader("📁 Carica un bilancio", type=["pdf", "xlsx", "xls"])

# Opzioni utente
use_gpt = st.checkbox("Usa fallback GPT se parser fallisce", value=False)
show_debug = st.checkbox("Mostra righe trovate e debug", value=True)

# Estrazione e analisi
if uploaded_file:
    file_path = "temp_uploaded_file"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())

    with st.spinner("Estrazione in corso..."):
        data, debug = extract_financial_data(file_path, return_debug=True, use_gpt=use_gpt)

    st.subheader("📄 Dati estratti")
    st.json(data)

    if "errore" in debug:
        st.error(f"Errore nel file: {debug['errore']}")

    # Debug e apprendimento
    if show_debug and "parser_debug" in debug:
        st.subheader("🔍 Debug Parser Avanzato")
        for voce, info in debug["parser_debug"].items():
            with st.expander(f"📌 {voce} - Scelto: {info['valore']} (score {info['score']})"):
                st.write(f"**Riga trovata:**")
                st.code(info["riga"])
                if st.button(f"✅ Conferma e salva riga per '{voce}'", key=f"save_{voce}"):
                    save_learned_pattern(voce, info["riga"], info["valore"])
                    st.success(f"✔ Pattern salvato per '{voce}'")

    # KPI
    if data:
        kpis = calculate_kpis(data)
        st.subheader("📈 KPI Calcolati")
        st.dataframe(kpis)

        st.subheader("📊 Grafico KPI")
        st.plotly_chart(plot_kpis(kpis), use_container_width=True)
