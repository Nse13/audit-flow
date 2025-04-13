# --- pages/5_Fatture_DDT.py ---
import streamlit as st
import datetime
import os
import sys

# Collegamento al modulo gestionale
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from gestionale.fatture import Documento, RegistroDocumenti

st.title("📄 Fatture e Documenti di Trasporto")

DOCUMENTI_FILE = "documenti.json"
registro = RegistroDocumenti()

# Caricamento documenti esistenti
if os.path.exists(DOCUMENTI_FILE):
    registro.carica_da_file(DOCUMENTI_FILE)

st.subheader("➕ Aggiungi documento")

with st.form("form_doc"):
    tipo = st.selectbox("Tipo documento", ["Fattura", "DDT"])
    numero = st.text_input("Numero documento")
    data = st.date_input("Data", value=datetime.date.today())
    cliente = st.text_input("Cliente / Destinatario")
    importo = st.number_input("Importo", step=100.0)
    descrizione = st.text_area("Descrizione")
    submit = st.form_submit_button("Aggiungi documento")

    if submit:
        doc = Documento(
            numero=numero,
            tipo=tipo,
            data=data.strftime("%Y-%m-%d"),
            cliente=cliente,
            importo=importo,
            descrizione=descrizione
        )
        registro.aggiungi_documento(doc)
        registro.salva_su_file(DOCUMENTI_FILE)
        st.success("✅ Documento salvato correttamente!")

st.markdown("### 🔍 Ricerca Fattura o DDT")

criteri = {
    "Numero": "numero",
    "Tipo": "tipo",
    "Data": "data",
    "Cliente": "cliente",
    "Importo": "importo",
    "Descrizione": "descrizione"
}

criterio = st.selectbox("Cerca per", list(criteri.keys()))
valore = st.text_input("Inserisci il valore da cercare")

if valore:
    risultati = [
        d for d in registro.to_list()
        if valore.lower() in str(d[criteri[criterio]]).lower()
    ]
    if risultati:
        st.success(f"Trovati {len(risultati)} risultati:")
        st.dataframe(risultati, use_container_width=True)
    else:
        st.warning("Nessuna corrispondenza trovata.")

st.markdown("### 📑 Elenco documenti registrati")

if registro.documenti:
    st.dataframe(registro.to_list(), use_container_width=True)
else:
    st.info("Nessun documento registrato.")
