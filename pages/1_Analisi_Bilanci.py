import streamlit as st
from utils import extract_financial_data, calculate_kpis, plot_kpis, salva_valore_confermato

st.title("📊 Analisi Bilanci Avanzata")
file = st.file_uploader("Carica bilancio PDF", type=["pdf"])
use_llm = st.checkbox("📌 Usa AuditLLM per analisi avanzata")

if file:
    with open("temp.pdf", "wb") as f:
        f.write(file.getbuffer())

    data = extract_financial_data("temp.pdf", use_llm=use_llm)

    st.subheader("📌 Conferma o correggi dati estratti:")
    updated_data = {}
    for k, v in data.items():
        new_val = st.text_input(f"{k}:", value=str(v))
        updated_data[k] = float(new_val)

        if new_val != str(v):
            salva_valore_confermato(k, float(new_val), f"valore originale:{v}")

    df_kpis = calculate_kpis(updated_data)
    st.dataframe(df_kpis)

    fig = plot_kpis(df_kpis)
    st.plotly_chart(fig)
