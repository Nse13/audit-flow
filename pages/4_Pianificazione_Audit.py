import streamlit as st

st.title("🧭 Pianificazione Audit & Materialità")
st.markdown("Definisci soglie di materialità, aree a rischio e note utili alla pianificazione della revisione.")

st.subheader("📏 Soglia di Materialità")
materialita_relativa = st.slider("Materialità Relativa (%)", 0.5, 10.0, 2.0, step=0.1)
materialita_assoluta = st.number_input("Materialità Assoluta (€)", min_value=0.0, step=1000.0, value=10000.0)

st.subheader("⚠️ Aree a Rischio Maggiore")
aree = ["Ricavi", "Crediti commerciali", "Magazzino", "Costi anticipati", "Immobilizzazioni", "Debiti vs fornitori", "Personale", "Leasing"]
aree_selezionate = st.multiselect("Seleziona le aree da approfondire", aree)

st.subheader("📝 Note di Pianificazione")
note = st.text_area("Inserisci qui le tue osservazioni, approcci, o obiettivi di revisione", height=150)

st.subheader("✅ Checklist ISA Semplificata")
isa_items = {
    "ISA 315 – Identificazione e valutazione del rischio": False,
    "ISA 330 – Risposte al rischio": False,
    "ISA 500 – Evidenza di revisione": False,
    "ISA 520 – Procedure analitiche": False,
}
checklist = {}
for item in isa_items:
    checklist[item] = st.checkbox(item)

if st.button("💾 Salva Pianificazione"):
    st.success("Pianificazione audit salvata! (Simulazione)")
    st.write("### 🔍 Riepilogo:")
    st.write(f"Materialità relativa: {materialita_relativa}%")
    st.write(f"Materialità assoluta: €{materialita_assoluta:,.2f}")
    st.write("Aree critiche selezionate:", aree_selezionate)
    st.write("Note:", note)
    st.write("Checklist ISA completata:", [k for k, v in checklist.items() if v])
