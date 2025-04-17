# --- pages/5_Fatture_DDT.py ---
import streamlit as st
import datetime
import os
import sys
import pandas as pd
import io

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

st.subheader("🔍 Ricerca e Filtri")
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
tipo_filtro = st.selectbox("Filtra per tipo", ["Tutti", "Fattura", "DDT"])

# Filtraggio documenti
documenti_filtrati = []
for doc in registro.documenti:
    match_tipo = (tipo_filtro == "Tutti") or (doc.tipo == tipo_filtro)
    match_query = valore.lower() in str(getattr(doc, criteri[criterio])).lower() if valore else True
    if match_tipo and match_query:
        documenti_filtrati.append(doc)

# Esportazione Excel
if documenti_filtrati:
    st.markdown("### ⬇️ Esporta in Excel")
    buffer = io.BytesIO()
    df = pd.DataFrame([vars(d) for d in documenti_filtrati])
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    st.download_button("📥 Scarica Documenti Excel", buffer, file_name="documenti.xlsx")

st.markdown("### 📋 Elenco documenti registrati")
if documenti_filtrati:
    for doc in documenti_filtrati:
        with st.expander(f"{doc.tipo} – {doc.numero} – {doc.cliente}"):
            st.write(f"📅 Data: {doc.data}")
            st.write(f"💰 Importo: € {doc.importo:,.2f}")
            st.write(f"📄 Descrizione: {doc.descrizione}")
            if st.button("🗑️ Elimina", key=f"del_{doc.numero}"):
                registro.documenti.remove(doc)
                registro.salva_su_file(DOCUMENTI_FILE)
                st.success("✅ Documento eliminato!")
                st.experimental_rerun()
else:
    st.info("Nessun documento trovato.")
