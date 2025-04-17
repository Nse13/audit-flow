# --- pages/5_Fatture_DDT.py ---
import streamlit as st
import datetime
import os
import sys
import json
import base64
import tempfile

# Collegamento al modulo gestionale
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from gestionale.fatture import Documento, RegistroDocumenti
from gestionale.movimenti import RegistroMovimenti, Movimento

st.title("📄 Fatture e Documenti di Trasporto")

DOCUMENTI_FILE = "documenti.json"
MOVIMENTI_FILE = "movimenti.json"
registro = RegistroDocumenti()
registro_movimenti = RegistroMovimenti()

if os.path.exists(DOCUMENTI_FILE):
    registro.carica_da_file(DOCUMENTI_FILE)
if os.path.exists(MOVIMENTI_FILE):
    registro_movimenti.carica_da_file(MOVIMENTI_FILE)

st.subheader("➕ Aggiungi documento")

with st.form("form_doc"):
    tipo = st.selectbox("Tipo documento", ["Fattura", "DDT"])
    numero = st.text_input("Numero documento")
    data = st.date_input("Data", value=datetime.date.today())
    cliente = st.text_input("Cliente / Destinatario")
    importo = st.number_input("Importo", step=100.0)
    descrizione = st.text_area("Descrizione")
    allegato = st.file_uploader("📎 Allega file (PDF o immagine)", type=["pdf", "png", "jpg", "jpeg"])
    crea_movimento = st.checkbox("Registra movimento contabile associato")
    submit = st.form_submit_button("Aggiungi documento")

    if submit:
        allegato_path = ""
        if allegato:
            estensione = os.path.splitext(allegato.name)[1]
            allegato_path = f"allegati/{tipo}_{numero}{estensione}"
            os.makedirs("allegati", exist_ok=True)
            with open(allegato_path, "wb") as f:
                f.write(allegato.read())

        doc = Documento(
            numero=numero,
            tipo=tipo,
            data=data.strftime("%Y-%m-%d"),
            cliente=cliente,
            importo=importo,
            descrizione=descrizione,
            allegato=allegato_path
        )
        registro.aggiungi_documento(doc)
        registro.salva_su_file(DOCUMENTI_FILE)

        if crea_movimento:
            movimento = Movimento(
                data=data.strftime("%Y-%m-%d"),
                descrizione=f"{tipo} {numero} - {cliente}",
                importo=importo,
                tipo="Entrata" if tipo == "Fattura" else "Uscita",
                documento_riferimento=numero
            )
            registro_movimenti.aggiungi_movimento(movimento)
            registro_movimenti.salva_su_file(MOVIMENTI_FILE)

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
    risultati = [d for d in registro.to_list() if valore.lower() in str(d[criteri[criterio]]).lower()]
    if risultati:
        st.success(f"Trovati {len(risultati)} risultati:")
        st.dataframe(risultati, use_container_width=True)
    else:
        st.warning("Nessuna corrispondenza trovata.")

st.markdown("### 📑 Elenco documenti registrati")

if registro.documenti:
    for doc in registro.documenti:
        with st.expander(f"📄 {doc.tipo} {doc.numero} – {doc.cliente}"):
            st.write(f"📅 Data: {doc.data}")
            st.write(f"💰 Importo: € {doc.importo:,.2f}")
            st.write(f"📝 Descrizione: {doc.descrizione}")
            if doc.allegato and os.path.exists(doc.allegato):
                with open(doc.allegato, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                    ext = os.path.splitext(doc.allegato)[1][1:]
                    href = f'<a href="data:application/{ext};base64,{b64}" download="{os.path.basename(doc.allegato)}">📎 Scarica allegato</a>'
                    st.markdown(href, unsafe_allow_html=True)
else:
    st.info("Nessun documento registrato.")
