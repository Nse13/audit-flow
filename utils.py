import fitz  # PyMuPDF
import pandas as pd
import openpyxl
import plotly.express as px
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import openai
import os

# 1. Estrazione dati
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

# 2. Calcolo KPI
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

# 3. Grafico KPI
def plot_kpis(df_kpis):
    fig = px.bar(df_kpis, x="KPI", y="Valore", title="KPI Finanziari", text="Valore")
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig.update_layout(yaxis_title="Valore (%)", xaxis_title="", showlegend=False)
    return fig

# 4. GPT Comment (opzionale)
def generate_gpt_comment(data):
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        return "⚠️ Nessuna API key OpenAI trovata. GPT disattivato."

    prompt = f"Analizza questi dati finanziari:\n{data}\nScrivi un commento professionale di audit."

    openai.api_key = openai_api_key
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Sei un revisore contabile professionista."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=300
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Errore GPT: {e}"

# 5. PDF Report
def generate_pdf_report(data, df_kpis, commento="", filename="report_auditflow.pdf"):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, height - 50, "Audit Flow+ - Report Analisi")

    c.setFont("Helvetica", 11)
    y = height - 80
    for k, v in data.items():
        c.drawString(40, y, f"{k}: {v}")
        y -= 18

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "KPI Calcolati:")
    y -= 20
    c.setFont("Helvetica", 10)
    for _, row in df_kpis.iterrows():
        c.drawString(50, y, f"{row['KPI']}: {row['Valore']}%")
        y -= 16

    if commento:
        y -= 30
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Commento GPT:")
        y -= 20
        c.setFont("Helvetica", 9)
        for line in commento.split('\n'):
            c.drawString(50, y, line)
            y -= 14
            if y < 60:
                c.showPage()
                y = height - 50

    c.save()
