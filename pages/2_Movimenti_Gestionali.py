import streamlit as st
import datetime
import json
import os
import sys

# Collegamento al modulo gestionale
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from gestionale.movimenti import MovimentoContabile, RegistroMovimenti

st.title("📂 Movimenti Gestionali")

# File locale per salvataggio persistente
DATA_FILE = "movimenti.json"
registro = RegistroMovimenti()

# Caricamento dati precedenti
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, encoding="utf-8") as f:
        try:
            lista = json.load(f)
            registro.carica_da_lista(lista)
        except Exception as e:
            st.error(f"Errore caricamento dati esistenti: {e}")

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
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([m.to_dict() for m in registro.movimenti], f, indent=2)
        st.success("✅ Movimento aggiunto correttamente!")

st.markdown("### 📋 Movimenti attuali")
if registro.movimenti:
    st.dataframe([m.to_dict() for m in registro.movimenti], use_container_width=True)
else:
    st.info("Nessun movimento ancora registrato.")

st.markdown("### Totali per categoria")
st.json(registro.totali_per_categoria())

st.markdown("### 💾 Esporta in CSV")
if st.button("Scarica CSV"):
    filename = "movimenti_export.csv"
    registro.esporta_csv(filename)
    with open(filename, "rb") as f:
        st.download_button("📥 Download file CSV", f, file_name=filename)

st.markdown("### 🔍 Verifica movimenti sospetti")
soglia = st.number_input("Soglia importo (default: 1.000.000)", value=1_000_000)
sospetti = registro.verifica_movimenti_sospetti(soglia)
if sospetti:
    st.warning("⚠️ Movimenti sospetti trovati:")
    st.dataframe([m.to_dict() for m in sospetti])
else:
    st.success("✅ Nessun movimento sospetto oltre la soglia.")

st.markdown("### 🔁 Verifica coerenza con registro esterno")
file_esterno = st.file_uploader("Carica file JSON (es. clienti, fornitori, banche)", type="json")
if file_esterno:
    try:
        registro_esterno = json.load(file_esterno)
        differenze = registro.verifica_incoerenze_con_registro(registro_esterno)
        if differenze:
            st.error("❌ Movimenti non trovati nel registro esterno:")
            st.dataframe([m.to_dict() for m in differenze])
        else:
            st.success("✅ Tutti i movimenti sono coerenti con il registro esterno.")
    except Exception as e:
        st.error(f"Errore nella lettura del file JSON: {e}")
