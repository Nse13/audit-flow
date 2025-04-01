import streamlit as st
from utils import extract_financial_data, extract_text_from_file

st.set_page_config(page_title="Audit Flow Pro+", layout="wide")
st.title("📊 Audit Flow Pro+")
st.subheader("Estrazione e analisi automatica da bilanci PDF/Excel")

uploaded_file = st.file_uploader("Carica un file", type=["pdf", "txt", "json"])
if uploaded_file:
    file_bytes = uploaded_file.read()
    text = extract_text_from_file(file_bytes, uploaded_file.name)
    data = extract_financial_data(text)
    st.subheader("📄 Dati estratti")
    st.json(data)