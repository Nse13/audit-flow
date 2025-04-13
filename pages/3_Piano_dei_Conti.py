# --- pages/3_Piano_dei_Conti.py ---

import streamlit as st
import os
import sys

# Import modulo gestionale
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from gestionale.piano_conti import PianoDeiConti, VoceConto

st.title("📘 Piano dei Conti")

DATA_FILE = "piano_conti.json"
piano = PianoDeiConti()
piano.carica_da_file(DATA_FILE)

# Aggiungi nuova voce
st.subheader("➕ Aggiungi una nuova voce")

with st.form("aggiungi_voce"):
    codice = st.text_input("Codice Conto", "1001")
    descrizione = st.text_input("Descrizione", "Cassa")
    tipo = st.selectbox("Tipo", ["Attivo", "Passivo", "Costi", "Ricavi"])
    categoria = st.text_input("Categoria", "Disponibilità")
    submitted = st.form_submit_button("Aggiungi")

    if submitted:
        if piano.cerca_voce(codice):
            st.error("⚠️ Codice già presente nel piano.")
        else:
            voce = VoceConto(codice, descrizione, tipo, categoria)
            piano.aggiungi_voce(voce)
            piano.salva_su_file(DATA_FILE)
            st.success("✅ Voce aggiunta correttamente!")

# Visualizza piano dei conti
st.subheader("📋 Piano dei conti attuale")
if piano.voci:
    st.dataframe(piano.to_list(), use_container_width=True)
else:
    st.info("Nessuna voce ancora inserita.")

# Rimuovi voce
st.subheader("🗑️ Rimuovi voce")
codice_da_rimuovere = st.text_input("Codice da rimuovere")
if st.button("Elimina"):
    voce = piano.cerca_voce(codice_da_rimuovere)
    if voce:
        piano.rimuovi_voce(codice_da_rimuovere)
        piano.salva_su_file(DATA_FILE)
        st.success(f"✅ Voce {codice_da_rimuovere} rimossa.")
    else:
        st.error("❌ Codice non trovato nel piano.")
