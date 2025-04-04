import streamlit as st

st.set_page_config(
    page_title="Audit Flow+",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Audit Flow+")
st.markdown("Benvenuto nella dashboard centrale dell'applicazione **Audit Flow+**.")
st.markdown("Utilizza il menu a sinistra per navigare tra le sezioni:")

st.markdown("""
- 📂 **Movimenti Gestionali**  
  Carica fatture, estratti conto e cassa per analisi contabile.

- 🧾 **Analisi Bilanci**  
  Carica PDF o Excel per calcolo KPI, analisi comparativa e commento GPT.

- 🧭 **Pianificazione Audit**  
  Imposta soglie di materialità e aree critiche da controllare.

- 📝 **Report & KPI**  
  Visualizza i risultati e genera il report finale in PDF.

---

👈 Se non vedi il menu laterale, clicca sull’icona in alto a sinistra.
""")

