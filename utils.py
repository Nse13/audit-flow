# Funzioni di supporto per estrazioni, calcoli, GPT, esportazioni, ecc.
import fitz  # PyMuPDF
import pandas as pd
import openpyxl
import plotly.express as px
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import openai
import os

# 1. ESTRAZIONE DATI DA PDF O EXCEL ----------------------
def extract_financial_data(file_path, return_debug=False):
    debug_info = {}
    data = {}

    if file_path.endswith(".pdf"):
        with fitz.open(file_path) as doc:
            text = ""
            for page in doc:
                text += page.get_text()
            debug_info["tipo_file"] = "PDF"
            debug_info["estratto"] = text[:1000]
            # MOCK estrazione semplificata
            data = {
                "Ricavi": 120000,
                "Costi": 75000,
                "Utile Netto": 32000,
                "Totale Attivo": 190000,
                "Patrimonio Netto": 95000
            }

    elif file_path.endswith((".xlsx", ".xls")):
        df = pd.read_excel(file_path)
        debug_info["tipo_file"] = "EXCEL"
        debug_info["colonne"] = df.columns.tolist()
        # MOCK: usa i primi valori se presenti
        try:
            data = {
                "Ricavi": float(df.iloc[0]["Ricavi"]),
                "Costi": float(df.iloc[0]["Costi"]),
                "Utile Netto": float(df.iloc[0]["Utile Netto"]),
                "Totale Attivo": float(df.iloc[0]["Totale Attivo"]),
                "Patrimonio Netto": float(df.iloc[0]["Patrimonio Netto"])
            }
        except Exception as e:
            debug_info["errore"] = str(e)

    return (data, debug_info) if return_debug else data

# 2. CALCOLO KPI FINANZIARI --------------------------------
def calculate_kpis(data):
    ricavi = data.get("Ricavi", 0)
    costi = data.get("Costi", 0)
    utile = data.get("Utile Netto", 0)
    attivo = data.get("Totale Attivo", 1)
    pn = data.get("Patrimonio Netto", 1)

    kpis = {
        "Margine Operativo (%)": round((ricavi - costi) / ricavi * 100, 2) if ricavi else 0,
        "Return on Equity (ROE)": round(utile / pn * 100, 2) if pn else 0,
        "Return on Assets (ROA)": round(utile / attivo * 100, 2) if attivo else 0,
        "Rapporto Ricavi/Attivo": round(ricavi / attivo, 2) if attivo else 0,
        "Indice di Efficienza": round(utile / costi * 100, 2) if costi else 0
    }
    return pd.DataFrame(list(kpis.items()), columns=["KPI", "Valore"])

# 3. GRAFICO INTERATTIVO KPI -------------------------------
def plot_kpis(df_kpis):
    fig = px.bar(df_kpis, x="KPI", y="Valore", title="KPI Finanziari", text="Valore")
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig.update_layout(yaxis_title="Valore (%)", xaxis_title="", showlegend=False)
    return fig

# 4. COMMENTO GPT (OPZIONALE) -------------------------------
def generate_g_
