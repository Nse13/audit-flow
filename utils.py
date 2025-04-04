import fitz  # PyMuPDF
import pandas as pd
import openai
import os
import plotly.express as px
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# Prova a importare OCR solo se disponibile
OCR_AVAILABLE = False
try:
    import pytesseract
    from PIL import Image
    import io
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    OCR_AVAILABLE = True
except ImportError:
    pass

# 1. Estrazione dati da PDF o Excel
def extract_financial_data(file_path, return_debug=False, use_gpt=False):
    debug_info = {}
    data = {}

    if file_path.endswith(".pdf"):
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                page_text = page.get_text().strip()
                if page_text:
                    text += page_text
                elif OCR_AVAILABLE:
                    pix = page.get_pixmap()
                    img = Image.open(io.BytesIO(pix.tobytes()))
                    text += pytesseract.image_to_string(img, lang="ita")
        debug_info["estratto"] = text[:1000]

        if use_gpt:
            data = extract_with_gpt(text)
        else:
            data = extract_with_keywords(text)

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

# 2. Estrazione testuale semplice
def extract_with_keywords(text):
    import re
    def find_val(keyword):
        match = re.search(rf"{keyword}[\s:€]*([\d\.,]+)", text, re.IGNORECASE)
        if match:
            val = match.group(1).replace(".", "").replace(",", ".")
            try:
                return float(val)
            except:
                return 0.0
        return 0.0

    return {
        "Ricavi": find_val("Ricavi"),
        "Costi": find_val("Costi"),
        "Utile Netto": find_val("Utile Netto"),
        "Totale Attivo": find_val("Totale Attivo"),
        "Patrimonio Netto": find_val("Patrimonio Netto")
    }

# 3. GPT (opzionale)
def extract_with_gpt(text):
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        return {"errore": "⚠️ API Key mancante per OpenAI"}

    openai.api_key = openai_api_key
    prompt = f"""Hai il seguente testo estratto da un bilancio PDF:
{text}

Estrai i valori numerici principali (in euro), nel formato JSON con le seguenti chiavi:
- Ricavi
- Costi
- Utile Netto
- Totale Attivo
- Patrimonio Netto
Rispondi solo con il JSON puro.
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Sei un esperto contabile."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=300
        )
        content = response.choices[0].message["content"]
        return eval(content)
    except Exception as e:
        return {"errore GPT": str(e)}

# 4. Calcolo KPI
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

# 5. Grafico KPI
def plot_kpis(df_kpis):
    fig = px.bar(df_kpis, x="KPI", y="Valore", title="KPI Finanziari", text="Valore")
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig.update_layout(yaxis_title="Valore (%)", xaxis_title="", showlegend=False)
    return fig

# 6. Genera PDF
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
