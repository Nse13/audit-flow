
def generate_recommendations(df):
    if "ROE" in df and df["ROE"].mean() < 10:
        return "🔍 Attenzione: ROE basso. Potrebbe indicare bassa redditività per gli azionisti."
    if "ROI" in df and df["ROI"].mean() < 5:
        return "📉 ROI inferiore al benchmark. Rivedere gli investimenti aziendali."
    if "Total Debts" in df and "Equity" in df:
        leverage = df["Total Debts"].mean() / df["Equity"].mean()
        if leverage > 2:
            return "⚠️ Leverage elevato. L'azienda è fortemente indebitata rispetto al capitale proprio."
    return "✅ Nessuna anomalia evidente. I KPI sono in linea con i parametri attesi."
