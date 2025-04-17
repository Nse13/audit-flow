# --- pages/7_Clienti_Fornitori.py ---
import streamlit as st
from gestionale.anagrafiche import carica_anagrafiche, aggiungi_anagrafica, elimina_anagrafica
import pandas as pd

st.set_page_config(page_title="Clienti & Fornitori", page_icon="🧾")
st.title("📇 Gestione Clienti e Fornitori")

st.subheader("➕ Aggiungi nuova anagrafica")

with st.form("form_nuovo"):
    tipo = st.selectbox("Tipo", ["Cliente", "Fornitore"])
    nome = st.text_input("Nome / Ragione Sociale")
    partita_iva = st.text_input("Partita IVA o CF")
    indirizzo = st.text_input("Indirizzo")
    email = st.text_input("Email")
    telefono = st.text_input("Telefono")
    submit = st.form_submit_button("Salva")

    if submit and nome:
        nuova = {
            "Tipo": tipo,
            "Nome": nome,
            "Partita IVA": partita_iva,
            "Indirizzo": indirizzo,
            "Email": email,
            "Telefono": telefono
        }
        aggiungi_anagrafica(nuova)
        st.success(f"{tipo} salvato con successo!")

st.subheader("📄 Elenco Clienti / Fornitori")
anagrafiche = carica_anagrafiche()

if anagrafiche:
    df = pd.DataFrame(anagrafiche)
    st.dataframe(df)

    with st.expander("🗑️ Elimina"):
        for i, riga in enumerate(anagrafiche):
            col1, col2 = st.columns([6, 1])
            with col1:
                st.write(f"{riga['Tipo']}: {riga['Nome']}")
            with col2:
                if st.button("❌", key=f"del_{i}"):
                    elimina_anagrafica(i)
                    st.experimental_rerun()
else:
    st.info("Nessuna anagrafica presente.")
