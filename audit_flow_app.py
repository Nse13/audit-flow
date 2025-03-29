
import streamlit as st
import pandas as pd
import fitz  # PyMuPDF per lettura PDF

st.set_page_config(page_title="Audit Flow", layout="wide")

st.markdown("# Audit Flow")
st.markdown("### Smart Financial Analysis")
st.markdown("---")

st.sidebar.header("📂 Carica un documento")
file = st.sidebar.file_uploader("Scegli un file Excel o PDF", type=["xlsx", "xls", "pdf"])

def estrai_testo_da_pdf(uploaded_file):
    testo = ""
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        for page in doc:
            testo += page.get_text()
    return testo

def analizza_excel(file_excel):
    df = pd.read_excel(file_excel)
    st.subheader("📊 Anteprima dati contabili")
    st.dataframe(df)

    st.subheader("📈 Analisi automatica")
    tot = df["Importo"].sum()
    doppioni = df[df.duplicated()]
    outlier = df[df["Importo"] > df["Importo"].mean() + 2 * df["Importo"].std()]

    st.write(f"**Totale Movimenti:** {tot:,.2f} €")
    st.write(f"**Transazioni Duplicate:** {len(doppioni)}")
    st.write(f"**Transazioni Anomale:** {len(outlier)}")

    if not doppioni.empty:
        st.markdown("### 🔁 Dettaglio duplicati")
        st.dataframe(doppioni)
    if not outlier.empty:
        st.markdown("### ⚠️ Dettaglio anomalie")
        st.dataframe(outlier)

if file:
    if file.type == "application/pdf":
        st.subheader("📄 Testo estratto dal bilancio PDF")
        testo = estrai_testo_da_pdf(file)
        st.text_area("Contenuto del bilancio", testo, height=300)
    else:
        analizza_excel(file)

st.markdown("---")
st.caption("© 2025 Audit Flow – Tutti i diritti riservati")
