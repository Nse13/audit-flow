# --- 6_Movimenti_Estesi.py ---
import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime
from io import BytesIO

DATA_PATH = "gestionale/movimenti_estesi.json"

# Inizializza dati se non esiste
if not os.path.exists(DATA_PATH):
    with open(DATA_PATH, "w") as f:
        json.dump([], f)

# Carica dati
with open(DATA_PATH, "r") as f:
    movimenti = json.load(f)

st.title("📌 Registro Movimenti Estesi")

# === Inserimento nuovo movimento ===
st.subheader("➕ Aggiungi Movimento")

with st.form("aggiungi_movimento"):
    data = st.date_input("Data", value=datetime.today())
    descrizione = st.text_input("Descrizione")
    tipo = st.selectbox("Tipo", ["Entrata", "Uscita"])
    importo = st.number_input("Importo", step=0.01)
    contropartita = st.text_input("Cliente/Fornitore")
    fattura_ddt = st.text_input("Numero Fattura/DDT")
    categoria = st.selectbox("Categoria", ["Vendita", "Acquisto", "Pagamento", "Incasso", "Altro"])
    conferma = st.form_submit_button("Salva")

    if conferma:
        nuovo = {
            "data": str(data),
            "descrizione": descrizione,
            "tipo": tipo,
            "importo": importo,
            "contropartita": contropartita,
            "fattura_ddt": fattura_ddt,
            "categoria": categoria
        }
        movimenti.append(nuovo)
        with open(DATA_PATH, "w") as f:
            json.dump(movimenti, f, indent=2)
        st.success("Movimento salvato con successo.")
        st.experimental_rerun()

# === Visualizzazione movimenti ===
st.subheader("📋 Elenco Movimenti")

df = pd.DataFrame(movimenti)
if not df.empty:
    df["data"] = pd.to_datetime(df["data"])
    df = df.sort_values("data", ascending=False)
    st.dataframe(df)

    if st.button("📤 Esporta in Excel"):
        output = BytesIO()
        df.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)
        st.download_button(
            label="⬇️ Scarica Excel",
            data=output,
            file_name="movimenti_estesi.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Nessun movimento registrato.")
