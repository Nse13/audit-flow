# === pages/4_Gestione_Inventario.py ===

import streamlit as st
import datetime
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gestionale.inventario import ProdottoMagazzino, Magazzino

st.title("🏷️ Gestione Inventario")

# Inizializzazione magazzino in session_state
if "magazzino" not in st.session_state:
    st.session_state.magazzino = Magazzino()

magazzino = st.session_state.magazzino

# Aggiunta prodotto
st.subheader("➕ Aggiungi nuovo prodotto")
with st.form("aggiungi_prodotto"):
    codice = st.text_input("Codice prodotto", "P001")
    descrizione = st.text_input("Descrizione", "Prodotto esempio")
    quantita = st.number_input("Quantità iniziale", min_value=0, step=1)
    prezzo = st.number_input("Prezzo unitario (€)", min_value=0.0, step=0.01, format="%.2f")
    categoria = st.selectbox("Categoria", ["Generico", "Materia prima", "Prodotto finito", "Componenti", "Altro"])
    submit = st.form_submit_button("Aggiungi")

    if submit:
        prodotto = ProdottoMagazzino(codice, descrizione, quantita, prezzo, categoria)
        magazzino.aggiungi_prodotto(prodotto)
        st.success("✅ Prodotto aggiunto al magazzino")

# Visualizzazione inventario
st.subheader("📦 Inventario attuale")
prodotti = magazzino.elenco_prodotti()
if prodotti:
    st.dataframe(prodotti, use_container_width=True)

    st.metric("📊 Valore totale inventario (€)", f"{magazzino.inventario_totale():,.2f}")
else:
    st.info("Nessun prodotto registrato in magazzino.")
