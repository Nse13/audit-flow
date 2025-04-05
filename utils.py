import fitz  # PyMuPDF
import pandas as pd
import plotly.express as px
import re

# ✅ Estrazione universale da PDF di bilanci
def extract_financial_data_from_pdf(file_path):
    patterns = {
        "Ricavi": [
            r"(?:Net revenues|Ricavi netti|Ricavi consolidati)[^\d€]{0,20}([\d.,]{4,})",
            r"(?:Total Revenues)[^\d€]{0,20}([\d.,]{4,})"
        ],
        "Utile Netto": [
            r"(?:Net profit|Utile netto|Net income)[^\d€]{0,20}([\d.,]{4,})"
        ],
        "Totale Attivo": [
            r"(?:TOTAL ASSETS|Totale attivo)[^\d€]{0,20}([\d.,]{4,})"
        ],
        "Patrimonio Netto": [
            r"(?:TOTAL EQUITY|Patrimonio netto|Equity)[^\d€]{0,20}([\d.,]{4,})"
        ]
    }

    risultati = {}
    with fitz.open(file_path) as doc:
        for page in doc:
            text = page.get_text()
            for voce, lista_pattern in patterns.items():
                if voce not in risultati:
                    for pattern in lista_pattern:
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            valore_str = match.group(1)
                            valore = float(valore_str.replace(".", "").replace(",", "."))
                            risultati[voce] = round(valore, 2)
                            break
            if len(risultati) == len(patterns):
                break
    return risultati

# ✅ Funzione principale per estrazione
def extract_financial_data(file_path, return_debug=False, use_gpt=False):
    data = {}
    debug_info = {}

    if file_path.endswith(".pdf"):
        data = extract_financial_data_from_pdf(file_path)
        debug_info["tipo_file"] = "PDF"
        debug_info["estratto"] = data
    elif file_path.endswith((".xlsx", ".xls")):
        try:
            df = pd.read_excel(file_path)
            debug_info["tipo_file"] = "EXCEL"
            debug_info["colonne"] = df.columns.tolist()
            data = {
                "Ricavi": float(df.iloc[0]["Ricavi"]),
                "Costi": float(df.iloc[0]["Costi"]),
                "Utile Netto": float(df.iloc[0]["Utile Netto"]),
                "Totale Attivo": float(df.iloc[0]["Totale Attivo"]),
                "Patrimonio Netto": float(df.iloc[0]["Patrimonio Netto"])
            }
        except Exception as e:
            debug_info["errore"] = str(e)
    else:
        debug_info["errore"] = "Formato non supportato"

    return (data, debug_info) if return_debug else data

# 📊 Calcolo KPI
def calculate_kpis(data):
    ricavi = data.get("Ricavi", 0)
    costi = data.get("Costi", 0)
    utile = data.get("Utile Netto", 0)
    attivo = data.get("Totale Attivo", 1)
    pn = data.get("Patrimonio Netto", 1)

    kpis = {
        "Margine Operativo (%)": round((ricavi - costi) / ricavi * 100, 2) if ricavi and costi else 0,
        "Return on Equity (ROE)": round(utile / pn * 100, 2) if pn else 0,
        "Return on Assets (ROA)": round(utile / attivo * 100, 2) if attivo else 0,
        "Rapporto Ricavi/Attivo": round(ricavi / attivo, 2) if attivo else 0,
        "Indice di Efficienza": round(utile / costi * 100, 2) if costi else 0
    }
    return pd.DataFrame(list(kpis.items()), columns=["KPI", "Valore"])

# 📈 Grafico KPI
def plot_kpis(df_kpis):
    fig = px.bar(df_kpis, x="KPI", y="Valore", title="KPI Finanziari", text="Valore")
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig.update_layout(yaxis_title="Valore (%)", xaxis_title="", showlegend=False)
    return fig
