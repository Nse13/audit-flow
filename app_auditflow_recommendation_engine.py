
import streamlit as st
import pandas as pd

def smart_recommendations(kpi_data, history_path="recommendation_memory.csv"):
    recommendations = []
    memory_df = None

    # Carica memoria passata se esiste
    try:
        memory_df = pd.read_csv(history_path)
    except:
        memory_df = pd.DataFrame(columns=["ROE", "Margin", "DebtEquity", "Feedback"])

    roe = kpi_data.get("ROE (%)", None)
    margin = kpi_data.get("Net Margin (%)", None)
    debt_equity = kpi_data.get("Debt to Equity", None)

    # Regole di raccomandazione intelligenti simulate
    if roe is not None:
        if roe > 15:
            recommendations.append("✅ ROE elevato: ottimo ritorno per gli azionisti.")
        elif roe < 5:
            recommendations.append("⚠️ ROE molto basso: attenzione alla redditività del capitale.")
        else:
            recommendations.append("ℹ️ ROE nella media: valuta miglioramenti operativi.")

    if margin is not None:
        if margin > 20:
            recommendations.append("✅ Margine netto eccellente.")
        elif margin < 5:
            recommendations.append("⚠️ Margine netto basso: attenzione ai costi e ai prezzi.")
        else:
            recommendations.append("ℹ️ Margine nella media.")

    if debt_equity is not None:
        if debt_equity > 2:
            recommendations.append("⚠️ Elevato rapporto Debito/Equity: possibile rischio finanziario.")
        elif debt_equity < 0.5:
            recommendations.append("✅ Struttura finanziaria solida e ben capitalizzata.")
        else:
            recommendations.append("ℹ️ Leva finanziaria in linea con gli standard.")

    # Simula "apprendimento": aggiunge a memoria i KPI analizzati
    memory_df = memory_df.append({
        "ROE": roe,
        "Margin": margin,
        "DebtEquity": debt_equity,
        "Feedback": " | ".join(recommendations)
    }, ignore_index=True)

    # Salva memoria aggiornata
    memory_df.to_csv(history_path, index=False)

    return recommendations
