
import streamlit as st
from llm_utils import chiedi_auditllm

st.set_page_config(page_title="AuditLLM Assistant", layout="centered")
st.title("🧠 AuditLLM - La tua AI offline")

st.markdown("Fai una domanda alla tua AI autonoma basata su Mistral 7B.")

prompt = st.text_area("📥 Inserisci il tuo prompt", height=200)

if st.button("🤖 Rispondi con AuditLLM") and prompt.strip():
    with st.spinner("AuditLLM sta pensando..."):
        risposta = chiedi_auditllm(prompt)
    st.subheader("📤 Risposta di AuditLLM:")
    st.write(risposta)
