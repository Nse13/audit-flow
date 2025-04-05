import fitz
import re
import json
import pandas as pd
import plotly.express as px
import pytesseract
from PIL import Image
import io
import os
from llm_utils import ask_auditllm

# Funzione OCR per PDF immagine
def extract_text_pdf(file_path):
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            page_text = page.get_text()
            if page_text.strip():
                text += page_text
            else:
                pix = page.get_pixmap()
                img = Image.open(io.BytesIO(pix.tobytes()))
                text += pytesseract.image_to_string(img, lang="ita+eng")
    return text

# Estrazione intelligente valori
def smart_extract_value(keyword, synonyms, text):
    candidates = []
    lines = text.split("\n")
    all_terms = [keyword.lower()] + [s.lower() for s in synonyms]

    for i, line in enumerate(lines):
        line_lower = line.lower()

        if not any(term in line_lower for term in all_terms):
            continue

        numbers = re.findall(r"[-+]?\d[\d.,]*", line)
        for num_str in numbers:
            if re.match(r'^(19|20)\d{2}$', num_str):  # Penalizzo gli anni
                continue

            val = float(num_str.replace(".", "").replace(",", "."))

            score = 0
            if keyword.lower() in line_lower:
                score += 5
            if any(s in line_lower for s in synonyms):
                score += 3
            if abs(line_lower.find(keyword.lower()) - line_lower.find(num_str)) < 25:
                score += 4
            if "€" in line or "eur" in line_lower:
                score += 3
            if val > 1000:
                score += 3
            if "totale" in line_lower or ":" in line:
                score += 2

            candidates.append({"valore": val, "score": score, "linea": line})

    if candidates:
        best = max(candidates, key=lambda x: x["score"])
        return best["valore"]
    return 0.0

# Estrazione generale valori da PDF
def extract_financial_data(file_path, use_llm=False):
    text = extract_text_pdf(file_path)

    keywords_map = {
        "Ricavi": ["totale ricavi", "revenues", "net revenues"],
        "Costi": ["totale costi", "operating costs", "costi operativi"],
        "Utile Netto": ["net profit", "utile netto", "risultato netto"],
        "Totale Attivo": ["totale attivo", "total assets"],
        "Patrimonio Netto": ["patrimonio netto", "equity"]
    }

    data = {}
    if use_llm:
        prompt = f"""
        Dal seguente testo estrai in formato JSON:
        Ricavi, Costi, Utile Netto, Totale Attivo, Patrimonio Netto:
        
        {text[:4000]}  # Limite tokens
        """
        response = ask_auditllm(prompt)
        data = json.loads(response)
    else:
        for key, synonyms in keywords_map.items():
            data[key] = smart_extract_value(key, synonyms, text)

    return data

# Salvataggio apprendimento progressivo
def salva_valore_confermato(voce, valore, contesto):
    record = {"voce": voce, "valore": valore, "contesto": contesto}
    with open("memoria_apprendimento.json", "a") as f:
        json.dump(record, f)
        f.write("\n")

# Calcolo KPI
def calculate_kpis(data):
    ricavi = data.get("Ricavi", 1)
    costi = data.get("Costi", 1)
    utile = data.get("Utile Netto", 1)
    attivo = data.get("Totale Attivo", 1)
    pn = data.get("Patrimonio Netto", 1)

    kpis = {
        "Margine Operativo (%)": round((ricavi - costi) / ricavi * 100, 2),
        "Return on Equity (ROE)": round(utile / pn * 100, 2),
        "Return on Assets (ROA)": round(utile / attivo * 100, 2),
        "Rapporto Ricavi/Attivo": round(ricavi / attivo, 2),
        "Indice di Efficienza": round(utile / costi * 100, 2)
    }
    return pd.DataFrame(list(kpis.items()), columns=["KPI", "Valore"])

# Grafico KPI
def plot_kpis(df_kpis):
    fig = px.bar(df_kpis, x="KPI", y="Valore", text="Valore")
    fig.update_layout(title="KPI Finanziari", yaxis_title="%", xaxis_title="")
    return fig
