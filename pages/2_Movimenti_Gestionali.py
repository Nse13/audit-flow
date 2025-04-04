import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from gestionale import MovimentoContabile, RegistroMovimenti
import datetime

st.title("📂 Movimenti Gestionali")

registro = RegistroMovimenti()

st.subheader("➕ Aggiungi un nuovo movimento")

with st.form("aggiungi_movimento"):
    codice = st.text_input("Codice movimento", "OIC_01")
    descrizione = st.text_input("Descrizione", "Fattura attiva")
    categoria = st.selectbox("Categoria", ["Vendite", "Acquisti", "Finanziamenti", "Cassa", "Banca"])
    data = st.date_input("Data", value=datetime.date.today())
    importo = st.number_input("Importo", step=100.0)
    valuta = st.selectbox("Valuta", ["EUR", "USD"])
    standard = st.selectbox("Standard", ["OIC", "IAS", "IFRS"])
    submitted = st.form_submit_button("Aggiungi movimento")

    if submitted:
        movimento = MovimentoContabile(
            codice=codice,
            descrizione=descrizione,
            categoria=categoria,
            data=data.strftime("%Y-%m-%d"),
            importo=importo,
            valuta=valuta,
            standard=standard
        )
        registro.aggiungi_movimento(movimento)
        st.success("Movimento aggiunto correttamente!")

st.subheader("📋 Movimenti attuali")

if registro.movimenti:
    st.dataframe([m.to_dict() for m in registro.movimenti])
else:
    st.info("Nessun movimento ancora caricato.")
