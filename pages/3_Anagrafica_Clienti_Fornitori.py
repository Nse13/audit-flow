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

st.subheader("🔍 Ricerca e Filtro")

search_query = st.text_input("Cerca (nome, codice, P.IVA, email, ecc.)")
tipo_filtro = st.selectbox("Filtra per tipo", ["Tutti", "Cliente", "Fornitore"])

voci_filtrate = []
for voce in registro.voci:
    match_tipo = (tipo_filtro == "Tutti") or (voce.tipo == tipo_filtro)
    match_query = (search_query.lower() in voce.codice.lower() or
                   search_query.lower() in voce.ragione_sociale.lower() or
                   search_query.lower() in voce.partita_iva.lower() or
                   search_query.lower() in voce.email.lower())
    if match_tipo and match_query:
        voci_filtrate.append(voce)

st.subheader("📋 Voci registrate")

if registro.voci:
    voci_visualizzate = [v for v in registro.voci if
                         ((tipo_filtro == "Tutti") or (v.tipo == tipo_filtro)) and
                         (search_query.lower() in v.codice.lower() or
                          search_query.lower() in v.ragione_sociale.lower() or
                          search_query.lower() in v.partita_iva.lower() or
                          search_query.lower() in v.email.lower())]

    if voci_visualizzate:
        st.write("Seleziona le voci da eliminare:")
        voci_da_eliminare = []

        for i, voce in enumerate(voci_visualizzate):
    with st.expander(f"📄 {voce.codice} – {voce.ragione_sociale}"):
        col1, col2 = st.columns([0.1, 0.9])
        with col1:
            elimina = st.checkbox("🗑️", key=f"del_{voce.codice}")
        with col2:
            with st.form(f"mod_{voce.codice}"):
                nuovo_codice = st.text_input("Codice", value=voce.codice)
                nuova_ragione = st.text_input("Ragione Sociale", value=voce.ragione_sociale)
                nuovo_tipo = st.selectbox("Tipo", ["Cliente", "Fornitore"], index=0 if voce.tipo == "Cliente" else 1)
                nuovo_indirizzo = st.text_input("Indirizzo", value=voce.indirizzo)
                nuova_piva = st.text_input("Partita IVA", value=voce.partita_iva)
                nuova_email = st.text_input("Email", value=voce.email)
                conferma = st.form_submit_button("💾 Salva modifiche")

                if conferma:
                    voce.codice = nuovo_codice
                    voce.ragione_sociale = nuova_ragione
                    voce.tipo = nuovo_tipo
                    voce.indirizzo = nuovo_indirizzo
                    voce.partita_iva = nuova_piva
                    voce.email = nuova_email
                    registro.salva_su_file(DATA_FILE)
                    st.success("✅ Modifiche salvate!")

    if elimina:
        registro.voci.remove(voce)
        registro.salva_su_file(DATA_FILE)
        st.success("✅ Voce eliminata.")
        st.experimental_rerun()


        if voci_da_eliminare:
            if st.button("🗑️ Elimina voci selezionate"):
                for voce in voci_da_eliminare:
                    registro.voci.remove(voce)
                registro.salva_su_file(DATA_FILE)
                st.success(f"{len(voci_da_eliminare)} voce/i eliminata/e correttamente!")
                st.experimental_rerun()
    else:
        st.info("Nessuna voce trovata per la ricerca e filtro selezionati.")
else:
    st.info("Nessuna voce registrata ancora.")
