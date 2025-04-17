# --- 6_Gestionale_Movimenti.py ---
import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Movimenti Contabili", page_icon="💼")
st.title("💼 Gestione Movimenti Contabili")

DB_FILE = "movimenti_contabili.json"

def carica_dati():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def salva_dati(movimenti):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(movimenti, f, indent=2, ensure_ascii=False)

# Carica dati esistenti
movimenti = carica_dati()

# Form per aggiungere un nuovo movimento
with st.form("nuovo_movimento"):
    st.subheader("➕ Aggiungi Movimento")
    data = st.date_input("📅 Data", value=datetime.today())
    descrizione = st.text_input("📝 Descrizione")
    conto_dare = st.text_input("🔻 Conto Dare")
    conto_avere = st.text_input("🔺 Conto Avere")
    importo = st.number_input("💰 Importo", min_value=0.01, step=0.01)

    submitted = st.form_submit_button("Salva")
    if submitted:
        if not (descrizione and conto_dare and conto_avere):
            st.error("Compila tutti i campi obbligatori.")
        else:
            nuovo = {
                "data": str(data),
                "descrizione": descrizione,
                "conto_dare": conto_dare,
                "conto_avere": conto_avere,
                "importo": round(importo, 2)
            }
            movimenti.append(nuovo)
            salva_dati(movimenti)
            st.success("✅ Movimento salvato con successo!")
            st.experimental_rerun()

# Visualizza movimenti esistenti
if movimenti:
    st.subheader("📋 Elenco Movimenti Registrati")
    df = pd.DataFrame(movimenti)
    st.dataframe(df)
else:
    st.info("Nessun movimento presente al momento.")
