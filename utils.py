import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import os
import json
import pandas as pd
import plotly.express as px
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from ollama import Client

client = Client()

OCR_AVAILABLE = True
CONFIRMED_DATA_PATH = "dati_confermati.json"

def extract_financial_data(file_path, return_debug=False, use_gpt=False):
    text = ""
    debug_info = {}

    if file_path.endswith(".pdf"):
        with fitz.open(file_path) as doc:
            for page in doc:
                page_text = page.get_text().strip()
                if not page_text and OCR_AVAILABLE:
                    pix = page.get_pixmap()
                    img = Image.open(io.BytesIO(pix.tobytes()))
                    text += pytesseract.image_to_string(img, lang="ita")
                else:
                    text += page_text
        debug_info["estratto"] = text[:2000]
        data = extract_all_values_smart(text)
        if use_gpt and all(v == 0 for v in data.values()):
            data = extract_with_gpt(text)
    else:
        debug_info["errore"] = f"Formato non supportato: {file_path}"
        data = {}

    return (data, debug_info) if return_debug else data


def smart_extract_value(keyword, synonyms, text):
    candidates = []
    lines = text.splitlines()
    all_terms = [keyword.lower()] + [s.lower() for s in synonyms]
    confirmed = carica_valori_confermati()

    if keyword in confirmed:
        return {"valore": confirmed[keyword], "score": 999, "riga": "🧠 Appreso"}

    for i, line in enumerate(lines):
        clean_line = line.strip()
        line_lower = clean_line.lower()
        found_term = next((t for t in all_terms if t in line_lower), None)
        if not found_term:
            continue

        import re
        numbers = re.findall(r"[-+]?\d[\d.,]*", clean_line)
        for num_str in numbers:
            try:
                val = float(num_str.replace(".", "").replace(",", "."))
            except:
                continue

            score = 0
            if keyword.lower() in line_lower: score += 3
            if found_term != keyword.lower(): score += 2
            if sum(t in line_lower for t in all_terms) == 1: score += 1
            if abs(line_lower.find(found_term) - line_lower.find(num_str)) < 25: score += 2
            if "€" in clean_line or ".00" in num_str or ",00" in num_str: score += 1
            if 1_000 <= val <= 10_000_000_000: score += 1
            if i < 15 or i > len(lines) - 15: score += 1
            if ":" in clean_line or "\t" in clean_line: score += 1
            if "totale" in line_lower: score += 2
            if val < 0 and any(t in line_lower for t in ["costo", "perdita", "oneri"]): score += 1
            if sum(t in text.lower() for t in all_terms) > 4: score -= 1
            if "%" in clean_line: score -= 1
            if "migliaia" in line_lower or "milioni" in line_lower: score += 1

            candidates.append({
                "term": found_term,
                "valore": val,
                "score": score,
                "riga": clean_line
            })

    best = sorted(candidates, key=lambda x: x["score"], reverse=True)
    return best[0] if best else {"valore": 0.0, "score": 0, "riga": ""}


def extract_all_values_smart(text):
    keywords_map = {
        "Ricavi": ["Totale ricavi", "Vendite", "Ricavi netti", "Proventi", "Revenues"],
        "Costi": ["Costi totali", "Spese", "Costi operativi", "Oneri", "Expenses"],
        "Utile Netto": ["Risultato netto", "Utile dell'esercizio", "Risultato d'esercizio", "Net Income"],
        "Totale Attivo": ["Totale attivo", "Attività totali", "Total Assets"],
        "Patrimonio Netto": ["Capitale proprio", "Patrimonio netto", "Equity", "Net Assets"]
    }

    results = {}
    for key, synonyms in keywords_map.items():
        results[key] = smart_extract_value(key, synonyms, text)["valore"]
    return results


def extract_with_gpt(text):
    try:
        prompt = f"""Nel seguente testo di bilancio, estrai i seguenti valori nel formato JSON:
- Ricavi
- Costi
- Utile Netto
- Totale Attivo
- Patrimonio Netto

Testo:
{text[:3000]}
"""
        response = client.chat(model="mistral", messages=[
            {"role": "user", "content": prompt}
        ])
        return json.loads(response['message']['content'])
    except Exception as e:
        return {"errore": str(e)}


def carica_valori_confermati():
    if os.path.exists(CONFIRMED_DATA_PATH):
        with open(CONFIRMED_DATA_PATH, "r") as f:
            return json.load(f)
    return {}

def salva_valore_confermato(chiave, valore):
    confermati = carica_valori_confermati()
    confermati[chiave] = valore
    with open(CONFIRMED_DATA_PATH, "w") as f:
        json.dump(confermati, f, indent=2)

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


def plot_kpis(df_kpis):
    fig = px.bar(df_kpis, x="KPI", y="Valore", title="KPI Finanziari", text="Valore")
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig.update_layout(yaxis_title="Valore (%)", xaxis_title="", showlegend=False)
    return fig
