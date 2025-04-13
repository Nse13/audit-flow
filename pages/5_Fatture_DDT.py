# --- pages/5_Fatture_DDT.py ---
import streamlit as st
import datetime
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from gestionale.fatture import Documento, RegistroDocumenti

st.title("📄 Fatture e DDT")

DOCUMENTI_FILE = "documenti.json"
registro = RegistroDocumenti()

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

st.subheader("📑 Elenco documenti registrati")

if registro.documenti:
    st.dataframe(registro.to_list(), use_container_width=True)
else:
    st.info("Nessun documento registrato.")
st.markdown("### 📄 Elenco Fatture e DDT registrati")

if registro_fatture.fatture:
    st.dataframe([f.to_dict() for f in registro_fatture.fatture], use_container_width=True)
else:
    st.info("Nessuna fattura o documento registrato.")
