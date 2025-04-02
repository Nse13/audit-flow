# gestionale.py
import streamlit as st
import pandas as pd

def dashboard_contabile(data):
    st.write("## 📌 Dashboard Gestionale Contabile")

    if not data:
        st.error("Nessun dato disponibile per la dashboard contabile.")
        return

    df_contabile = pd.DataFrame({
        'Elemento': list(data.keys()),
        'Valore': list(data.values())
    })

    st.table(df_contabile)

    # Calcoli aggiuntivi (esempi semplici per dimostrazione)
    st.write("### ⚖️ Bilanciamento Patrimoniale")
    try:
        totale_attivo = data.get("Total Assets", 0)
        totale_passivo = data.get("Total Debts", 0) + data.get("Equity", 0)
        differenza = totale_attivo - totale_passivo

        col1, col2, col3 = st.columns(3)
        col1.metric("Totale Attivo", f"{totale_attivo:,.2f}")
        col2.metric("Totale Passivo", f"{totale_passivo:,.2f}")
        col3.metric("Differenza", f"{differenza:,.2f}")

        if abs(differenza) < 1:
            st.success("Bilancio patrimoniale bilanciato correttamente.")
        else:
            st.warning("Attenzione: bilancio patrimoniale non bilanciato.")
    except Exception as e:
        st.error(f"Errore calcolo patrimoniale: {e}")

    # Ulteriori controlli rapidi
    st.write("### 📅 Analisi Rapida Dati Contabili")
    if "Revenue" in data and "Net Income" in data:
        margine_netto = round(data["Net Income"] / data["Revenue"] * 100, 2)
        st.write(f"- **Margine Netto:** {margine_netto}%")

    if "EBITDA" in data and "Revenue" in data:
        margine_ebitda = round(data["EBITDA"] / data["Revenue"] * 100, 2)
        st.write(f"- **Margine EBITDA:** {margine_ebitda}%")
