import fitz  # PyMuPDF
import pandas as pd
import plotly.express as px
import re

# ✅ Estrazione ottimizzata per bilanci PDF (es. Stellantis)
def extract_financial_data_from_pdf(file_path):
    patterns = {
        "Ricavi": [r"(ricavi netti|net revenues)[^\d]{0,20}([\d.,]{5,})"],
        "Utile Netto": [r"(utile netto|net profit|net income)[^\d]{0,20}([\d.,]{5,})"],
        "Totale Attivo": [r"(totale attivo|total assets)[^\d]{0,20}([\d.,]{5,})"],
        "Patrimonio Netto": [r"(patrimonio netto|total equity)[^\d]{0,20}([\d.,]{5,})"]
    }

    risultati = {}
    with fitz.open(file_path) as doc:
        for page in doc:
            text = page.get_text().lower().replace("€", "").replace(" ", " ").strip()

            for voce, lista in patterns.items():
                if voce in risultati:
                    continue
                for pattern in lista:
                    match = re.search(pattern, text)
                    if match:
                        raw_val = match.group(2).replace(".", "").replace(",", ".")
                        try:
                            risultati[voce] = round(float(raw_val), 2)
                        except:
                            pass
            if len(risultati) == 4:
                break
    return risultati

# ✅ Funzione principale
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
