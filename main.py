
import streamlit as st
from utils import extract_financial_data

st.set_page_config(page_title="Audit Flow Pro+", layout="wide")
st.title("📊 Audit Flow Pro+")
st.subheader("Estrazione e analisi automatica da bilanci PDF/Excel")

uploaded_file = st.file_uploader("Carica un file", type=["pdf", "txt", "json"])
if uploaded_file:
    text = uploaded_file.read().decode("utf-8")
    data = extract_financial_data(text)
    st.subheader("📄 Dati estratti")
    st.json(data)
