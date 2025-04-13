# --- pages/3_Anagrafica_Clienti_Fornitori.py ---

import streamlit as st
import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from gestionale.anagrafica import AnagraficaVoce, RegistroAnagrafica

st.title("📇 Anagrafica Clienti e Fornitori")

DATA_FILE = "anagrafica.json"
registro = RegistroAnagrafica()

if os.path.exists(DATA_FILE):
    registro.carica_da_file(DATA_FILE)

st.subheader("➕ Aggiungi Cliente o Fornitore")

with st.form("aggiungi_voce"):
    codice = st.text_input("Codice univoco", "")
    ragione_sociale = st.text_input("Ragione sociale", "")
    tipo = st.selectbox("Tipo", ["Cliente", "Fornitore"])
    indirizzo = st.text_input("Indirizzo", "")
    partita_iva = st.text_input("Partita IVA", "")
    email = st.text_input("Email", "")
    submit = st.form_submit_button("Aggiungi")

    if submit:
        nuova_voce = AnagraficaVoce(
            codice=codice,
            ragione_sociale=ragione_sociale,
            tipo=tipo,
            indirizzo=indirizzo,
            partita_iva=partita_iva,
            email=email
        )
        registro.aggiungi_voce(nuova_voce)
        registro.salva_su_file(DATA_FILE)
        st.success("✅ Voce aggiunta correttamente!")

st.subheader("📋 Voci registrate")

if registro.voci:
    st.dataframe(registro.to_list(), use_container_width=True)
else:
    st.info("Nessuna voce registrata ancora.")
