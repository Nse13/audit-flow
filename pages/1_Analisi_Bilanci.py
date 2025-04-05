import streamlit as st
import os
import sys
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import re
import io
import json

# ✅ Percorso Tesseract (necessario solo su Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

# ✅ Funzione OCR per pagine immagine del PDF
def ocr_page(page):
    pix = page.get_pixmap()
    img = Image.open(io.BytesIO(pix.tobytes()))
    return pytesseract.image_to_string(img, lang='ita')

# ✅ Estrazione testo da PDF (OCR + testo nativo)
def estrai_testo_pdf(file_path):
    testo = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text_page = page.get_text()
            if text_page.strip():
                testo += text_page
            else:
                testo += ocr_page(page)
    return testo

# ✅ Sinonimi delle voci contabili principali
synonyms = {
    "Ricavi": ["Totale ricavi", "Vendite", "Fatturato", "Revenues"],
    "Costi": ["Costi totali", "Spese operative", "Operating costs"],
    "Utile Netto": ["Risultato netto", "Profitto netto", "Net income"],
    "Totale Attivo": ["Attività totali", "Totale attività", "Total assets"],
    "Patrimonio Netto": ["Capitale proprio", "Equity", "Patrimonio netto"]
}

# ✅ Parser semantico: trova numeri associati ai sinonimi
def extract_financial_values(text, synonyms):
    estratti = {}
    for key, syns in synonyms.items():
        pattern = r"(?i)(" + "|".join(re.escape(s) for s in syns) + r")[^\d\n]*?([\d\.,]+)"
        matches = re.findall(pattern, text)
        if matches:
            valore_raw = matches[0][1].replace(".", "").replace(",", ".")
            try:
                estratti[key] = float(valore_raw)
            except:
                estratti[key] = 0.0
        else:
            estratti[key] = 0.0
    return estratti

# ✅ App Streamlit
st.set_page_config(page_title="Estrazione & Revisione Bilancio", layout="centered")
st.title("📊 Estrazione Dati Bilancio - Modalità Esperta")

uploaded_file = st.file_uploader("📁 Carica un bilancio PDF", type=["pdf"])

if uploaded_file:
    with open("tempfile.pdf", "wb") as f:
        f.write(uploaded_file.read())

    with st.spinner("📄 Estrazione testo e dati in corso..."):
        testo = estrai_testo_pdf("tempfile.pdf")
        dati_auto = extract_financial_values(testo, synonyms)

    st.subheader("🔍 Dati Estratti Automaticamente")
    st.write("Correggi i valori se necessario:")

    dati_confermati = {}
    for voce, valore in dati_auto.items():
        input_val = st.number_input(f"{voce}", value=valore, step=1000.0)
        dati_confermati[voce] = input_val

    if st.button("✅ Conferma e Salva"):
        with open("dati_confermati.json", "w") as f:
            json.dump(dati_confermati, f, indent=2)
        st.success("✔️ Dati confermati e salvati in 'dati_confermati.json'")
