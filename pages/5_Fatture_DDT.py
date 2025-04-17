# --- pages/5_Fatture_DDT.py ---
import streamlit as st
import datetime
import os
import sys
import io
import pandas as pd

# Collegamento al modulo gestionale
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from gestionale.fatture import Documento, RegistroDocumenti

st.title("📄 Fatture e Documenti di Trasporto")

DOCUMENTI_FILE = "documenti.json"
registro = RegistroDocumenti()

# Caricamento documenti esistenti
if os.path.exists(DOCUMENTI_FILE):
    registro.carica_da_file(DOCUMENTI_FILE)

# Aggiunta documento
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

# 📅 Filtro per periodo
st.subheader("📆 Filtro per Periodo")

data_inizio = st.date_input("Data inizio", value=datetime.date.today().replace(day=1))
data_fine = st.date_input("Data fine", value=datetime.date.today())

docs_filtrati = [
    d for d in registro.documenti
    if data_inizio <= datetime.datetime.strptime(d.data, "%Y-%m-%d").date() <= data_fine
]

# 🔍 Ricerca
st.subheader("🔍 Ricerca Fattura o DDT")

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
    docs_filtrati = [
        d for d in docs_filtrati
        if valore.lower() in str(getattr(d, criteri[criterio])).lower()
    ]

# 📊 Dashboard riepilogativa
st.subheader("📊 Riepilogo Statistico")

if docs_filtrati:
    df_docs = pd.DataFrame([vars(d) for d in docs_filtrati])
    fatturato_totale = df_docs["importo"].sum()
    media_per_tipo = df_docs.groupby("tipo")["importo"].mean().round(2)

    st.metric("💰 Totale documenti", f"{fatturato_totale:,.2f} €")
    st.write("📈 Media importo per tipo:")
    st.dataframe(media_per_tipo.reset_index().rename(columns={"tipo": "Tipo", "importo": "Media Importo (€)"}))

    # 📥 Esportazione Excel
    st.subheader("⬇️ Esporta dati")
    buffer = io.BytesIO()
    df_docs.to_excel(buffer, index=False)
    buffer.seek(0)
    st.download_button("📤 Scarica Excel", buffer, file_name="documenti_filtrati.xlsx")

    # 📑 Elenco documenti
    st.subheader("📋 Documenti filtrati")
    st.dataframe(df_docs, use_container_width=True)
else:
    st.info("Nessun documento trovato per i criteri selezionati.")
