import fitz  # PyMuPDF
import pandas as pd
import openai
import os
import plotly.express as px
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import re
import json

# ✅ OCR (Tesseract)
OCR_AVAILABLE = False
try:
    import pytesseract
    from PIL import Image
    import io
    pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
    OCR_AVAILABLE = True
except ImportError:
    pass

# ✅ OpenAI client
from openai import OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# 📌 Apprendimento locale (file json)
LEARNING_FILE = "learned_patterns.json"
def load_learned_patterns():
    if os.path.exists(LEARNING_FILE):
        with open(LEARNING_FILE, "r") as f:
            return json.load(f)
    return {}

def save_learned_pattern(label, riga, valore):
    patterns = load_learned_patterns()
    if label not in patterns:
        patterns[label] = []
    patterns[label].append({"riga": riga, "valore": valore})
    with open(LEARNING_FILE, "w") as f:
        json.dump(patterns, f, indent=2)

# 🔍 Parser intelligente
def smart_extract_value(label, synonyms, text, learned_data=None, return_candidates=False):
    candidates = []
    lines = text.split("\n")
    all_terms = [label.lower()] + [s.lower() for s in synonyms]

    # 1. Controlla pattern appresi
    if learned_data and label in learned_data:
        for item in learned_data[label]:
            if item["riga"] in text:
                return {"valore": item["valore"], "score": 999, "riga": item["riga"]}

    # 2. Scansione testo
    for i, line in enumerate(lines):
        clean_line = line.strip()
        line_lower = clean_line.lower()
        found_term = next((term for term in all_terms if term in line_lower), None)
        if not found_term:
            continue

        # Regex numeri + "milioni"
        raw_nums = re.findall(r"([-+]?\d[\d.,]+)\s*(milioni|mld|miliardi)?", clean_line)
        for num_str, tag in raw_nums:
            try:
                val = float(num_str.replace(".", "").replace(",", "."))
                if tag in ["milioni", "mld", "miliardi"]:
                    val *= 1_000_000
            except:
                continue

            score = 0
            if label.lower() in line_lower: score += 3
            if found_term != label.lower(): score += 2
            if sum(term in line_lower for term in all_terms) == 1: score += 1
            if abs(line_lower.find(found_term) - line_lower.find(num_str)) < 25: score += 2
            if "€" in clean_line or ".00" in num_str or ",00" in num_str: score += 1
            if 1_000 <= val <= 10_000_000_000: score += 1
            if i < 15 or i > len(lines) - 15: score += 1
            if ":" in clean_line or "\t" in clean_line: score += 1
            if "totale" in line_lower: score += 2
            if val < 0 and any(term in line_lower for term in ["costo", "perdita", "oneri"]): score += 1
            if sum(term in text.lower() for term in all_terms) > 4: score -= 1

            candidates.append({
                "term": found_term, "valore": val,
                "score": score, "riga": clean_line
            })

    best = sorted(candidates, key=lambda x: x["score"], reverse=True)
    if return_candidates:
        return best
    return best[0] if best else {"valore": 0.0, "score": 0, "riga": ""}
# 🔄 Cicla su tutte le voci
def extract_all_values_smart(text):
    keywords_map = {
        "Ricavi": ["Totale ricavi", "Revenues", "Vendite", "Ricavi netti", "Net sales"],
        "Costi": ["Costi totali", "Spese", "Operating costs", "Costi operativi", "Oneri"],
        "Utile Netto": ["Risultato netto", "Utile dell'esercizio", "Net Income", "Guadagno netto"],
        "Totale Attivo": ["Totale attivo", "Attività totali", "Total assets"],
        "Patrimonio Netto": ["Capitale proprio", "Patrimonio netto", "Equity", "PN"]
    }

    data = {}
    debug = {}
    learned = load_learned_patterns()
    for key, synonyms in keywords_map.items():
        best = smart_extract_value(key, synonyms, text, learned_data=learned)
        data[key] = best["valore"]
        debug[key] = best
    return data, debug

# 📌 Estrazione principale
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
        debug_info["estratto"] = text[:2000]

        if use_gpt:
            data = extract_with_gpt(text)
            debug_info["gpt"] = True
        else:
            data, debug = extract_all_values_smart(text)
            debug_info["parser_debug"] = debug
            debug_info["gpt"] = False

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

# 🤖 GPT fallback
def extract_with_gpt(text):
    try:
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
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Sei un esperto contabile."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=300
        )
        return eval(response.choices[0].message.content.strip())
    except Exception as e:
        return {"errore GPT": str(e)}

# 📊 Calcolo KPI
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

# 📈 Grafico KPI
def plot_kpis(df_kpis):
    fig = px.bar(df_kpis, x="KPI", y="Valore", title="KPI Finanziari", text="Valore")
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig.update_layout(yaxis_title="Valore (%)", xaxis_title="", showlegend=False)
    return fig

# 📄 PDF report
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
