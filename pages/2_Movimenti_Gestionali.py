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
