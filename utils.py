import re
import plotly.express as px

def extract_financial_data(text):
    try:
        data = {}
        patterns = {
            "Revenue": r"Revenue[^\d]*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)",
            "Net Income": r"Net Income[^\d]*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)",
            "EBITDA": r"EBITDA[^\d]*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)",
            "Total Assets": r"Total Assets[^\d]*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)",
            "Equity": r"Equity[^\d]*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)",
            "Total Debts": r"Total Debts[^\d]*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)",
            "Operating Costs": r"Operating Costs[^\d]*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)",
            "Cash Flow": r"Cash Flow[^\d]*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)",
            "Investments": r"Investments[^\d]*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)",
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).replace(".", "").replace(",", ".")
                data[key] = round(float(value))
        return data if data else {"ERROR": {"message": "Nessun valore rilevato"}}
    except Exception as e:
        return {"ERROR": {"message": str(e)}}

def generate_kpi_charts(data):
    import pandas as pd
    df = pd.DataFrame.from_dict(data, orient='index', columns=["Value"])
    df.reset_index(inplace=True)
    df.columns = ["KPI", "Value"]
    fig = px.bar(df, x="KPI", y="Value", title="Visualizzazione KPI")
    return fig