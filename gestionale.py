# Modulo contabile gestionale avanzato (inc# gestionale.py
import streamlit as st
import pandas as pd

def dashboard_contabile(data):
    st.write("## 📌 Dashboard Gestionale Contabile")

    if not data:
        st.error("Nessun dato disponibile per la dashboard contabile.")
        return

    df_contabile = pd.DataFrame({
        'Elemento': data.keys(),
        'Valore': data.values()
    })

    st.table(df_contabile)

    # Calcoli aggiuntivi (esempi semplici per dimostrazione)
    st.write("### ⚖️ Bilanciamento Patrimoniale")
    try:
        totale_attivo = data.get("Total Assets", 0)
        totale_passivo = data.get("Total Debts", 0) + data.get("Equity", 0)
        differenza = totale_attivo - totale_passivo

        st.metric("Totale Attivo", f"{totale_attivo:,.2f}")
        st.metric("Totale Passivo (Debiti + Equity)", f"{totale_passivo:,.2f}")
        st.metric("Differenza (Attivo - Passivo)", f"{differenza:,.2f}")

        if abs(differenza) < 1:
            st.success("Bilancio patrimoniale correttamente bilanciato!")
        else:
            st.warning("Attenzione: bilancio patrimoniale non perfettamente bilanciato.")
    except Exception as e:
        st.error(f"Errore nei calcoli patrimoniali: {e}")

    # Altri controlli contabili utili
    st.write("### 📅 Analisi Rapida Dati Contabili")
    if "Revenue" in data and "Net Income" in data:
        st.write(f"- **Margine Netto**: {round(data['Net Income'] / data['Revenue'] * 100, 2)}%")

    if "EBITDA" in data and "Revenue" in data:
        st.write(f"- **Margine EBITDA**: {round(data['EBITDA'] / data['Revenue'] * 100, 2)}%")
lusivo IAS/IFRS/OIC)
