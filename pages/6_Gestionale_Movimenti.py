import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime

MOVIMENTI_FILE = "gestionale/movimenti_estesi.json"
CLIENTI_FORNITORI_FILE = "gestionale/clienti_fornitori.json"
FATTURE_FILE = "gestionale/fatture_ddt.json"

st.title("📘 Registro Movimenti Contabili Estesi")

# Caricamento dati esistenti
if os.path.exists(MOVIMENTI_FILE):
    with open(MOVIMENTI_FILE, "r") as f:
        movimenti = json.load(f)
else:
    movimenti = []

# Carica clienti/fornitori
if os.path.exists(CLIENTI_FORNITORI_FILE):
    with open(CLIENTI_FORNITORI_FILE) as f:
        anagrafica = json.load(f)
    clienti_fornitori = [cf["nome"] for cf in anagrafica]
else:
    clienti_fornitori = []

# Carica fatture/DDT
if os.path.exists(FATTURE_FILE):
    with open(FATTURE_FILE) as f:
        fatture_ddt = json.load(f)
    opzioni_fatture = [f"{f['tipo']} {f['numero']} del {f['data']}" for f in fatture_ddt]
else:
    opzioni_fatture = []

st.subheader("➕ Aggiungi nuovo movimento")

col1, col2 = st.columns(2)
with col1:
    data = st.date_input("Data", value=datetime.today())
    tipo = st.selectbox("Tipo Movimento", ["Entrata", "Uscita"])
    importo = st.number_input("Importo (€)", step=0.01, format="%.2f")
    categoria = st.text_input("Categoria (es. Fattura, Acquisto, Stipendio...)")

with col2:
    cliente_fornitore = st.selectbox("Cliente/Fornitore (opzionale)", [""] + clienti_fornitori)
    fattura_collegata = st.selectbox("Collega Fattura/DDT (opzionale)", [""] + opzioni_fatture)
    descrizione = st.text_area("Descrizione", height=100)

if st.button("💾 Salva movimento"):
    nuovo = {
        "data": str(data),
        "tipo": tipo,
        "importo": importo,
        "categoria": categoria,
        "cliente_fornitore": cliente_fornitore,
        "fattura_collegata": fattura_collegata,
        "descrizione": descrizione
    }
    movimenti.append(nuovo)
    with open(MOVIMENTI_FILE, "w") as f:
        json.dump(movimenti, f, indent=2)
    st.success("✅ Movimento salvato!")

# Visualizza
st.subheader("📋 Storico movimenti")
df = pd.DataFrame(movimenti)
if not df.empty:
    st.dataframe(df)
    st.download_button("⬇️ Esporta in Excel", df.to_csv(index=False).encode(), file_name="movimenti_estesi.csv", mime="text/csv")
else:
    st.info("Nessun movimento registrato.")

