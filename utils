import fitz  # PyMuPDF
import pandas as pd
import plotly.express as px
import os
import json
import re

OCR_AVAILABLE = False
try:
    import pytesseract
    from PIL import Image
    import io
    OCR_AVAILABLE = True
except ImportError:
    pass

CONFIRMATION_DB = "confermati.json"
def salva_valore_confermato(chiave, testo, valore):
    if not os.path.exists(CONFIRMATION_DB):
        with open(CONFIRMATION_DB, "w") as f:
            json.dump({}, f)
    with open(CONFIRMATION_DB) as f:
        db = json.load(f)
    if chiave not in db:
        db[chiave] = []
    db[chiave].append({"testo": testo, "valore": valore})
    with open(CONFIRMATION_DB, "w") as f:
        json.dump(db, f, indent=2)

def check_valori_confermati(text, chiave):
    if not os.path.exists(CONFIRMATION_DB):
        return None
    with open(CONFIRMATION_DB) as f:
        db = json.load(f)
    candidati = db.get(chiave, [])
    for c in candidati:
        if c.get("testo") and c["testo"] in text:
            return c["valore"]
    return None

def smart_extract_value(keyword, synonyms, text):
    candidates = []
    lines = text.split("\n")
    all_terms = [keyword.lower()] + [s.lower() for s in synonyms]

    for i, line in enumerate(lines):
        line_lower = line.lower()
        found_term = next((term for term in all_terms if term in line_lower), None)
        if not found_term:
            continue

        numbers = re.findall(r"[-+]?\d[\d.,]+", line)
        for num_str in numbers:
            try:
                val = float(num_str.replace(".", "").replace(",", "."))
            except:
                continue

            if "million" in line_lower or "milioni" in line_lower:
                val *= 1_000_000

            score = 0
            if keyword.lower() in line_lower: score += 4
            if found_term != keyword.lower(): score += 2
            if sum(term in line_lower for term in all_terms) == 1: score += 1
            if abs(line_lower.find(found_term) - line_lower.find(num_str)) < 25: score += 2
            if "€" in line or ".00" in num_str or ",00" in num_str: score += 1
            if 1_000 <= val <= 100_000_000_000: score += 1
            if i < 10 or i > len(lines) - 10: score += 1
            if ":" in line or "\t" in line: score += 1
            if "totale" in line_lower: score += 2
            if val < 0 and any(x in line_lower for x in ["perdita", "costo", "oneri"]): score += 1
            if any(x in line_lower for x in ["2023", "2022", "2024"]): score -= 3
            if "consolidated" in line_lower: score += 1
            if "statement" in line_lower or "income" in line_lower or "balance" in line_lower: score += 2
            if "note" in line_lower: score -= 2

            candidates.append({"term": found_term, "valore": val, "score": score, "riga": line})

    best = sorted(candidates, key=lambda x: x["score"], reverse=True)
    return best[0] if best else {"valore": 0.0, "score": 0, "riga": ""}

def extract_all_values_smart(text):
    keywords_map = {
        "Ricavi": ["Totale ricavi", "Revenue", "Vendite", "Net revenues"],
        "Costi": ["Costi totali", "Total expenses", "Oneri", "Spese operative"],
        "Utile Netto": ["Utile netto", "Net income", "Risultato d'esercizio"],
        "Totale Attivo": ["Total assets", "Totale attivo", "Attività"],
        "Patrimonio Netto": ["Total equity", "Patrimonio netto", "Equity"],
        "Debiti Totali": ["Total liabilities", "Passività totali", "Debiti"],
        "Cassa": ["Cash", "Cassa e disponibilità liquide", "Disponibilità liquide"],
        "EBITDA": ["EBITDA", "Risultato operativo lordo"],
        "Flusso di cassa operativo": ["Operating cash flow", "Flusso di cassa operativo"]
    }
    risultati = {}
    for key, synonyms in keywords_map.items():
        confermato = check_valori_confermati(text, key)
        if confermato is not None:
            risultati[key] = confermato
        else:
            estratto = smart_extract_value(key, synonyms, text)
            risultati[key] = estratto["valore"]
    return risultati

def extract_financial_data(file_path, return_debug=False):
    debug_info = {}
    data = {}

    if file_path.endswith(".pdf"):
        text = ""
        try:
            with fitz.open(file_path) as doc:
                for page in doc:
                    t = page.get_text()
                    if not t and OCR_AVAILABLE:
                        pix = page.get_pixmap()
                        img = Image.open(io.BytesIO(pix.tobytes()))
                        t = pytesseract.image_to_string(img, lang="ita")
                    text += t + "\n"
        except Exception as e:
            debug_info["errore"] = f"Errore apertura PDF: {str(e)}"
            return (data, debug_info) if return_debug else data

        debug_info["estratto"] = text[:2000]
        data = extract_all_values_smart(text)

    elif file_path.endswith(('.xlsx', '.xls')):
        try:
            df = pd.read_excel(file_path)
            data = {
                "Ricavi": float(df.iloc[0].get("Ricavi", 0)),
                "Costi": float(df.iloc[0].get("Costi", 0)),
                "Utile Netto": float(df.iloc[0].get("Utile Netto", 0)),
                "Totale Attivo": float(df.iloc[0].get("Totale Attivo", 0)),
                "Patrimonio Netto": float(df.iloc[0].get("Patrimonio Netto", 0)),
                "Debiti Totali": float(df.iloc[0].get("Debiti Totali", 0)),
                "Cassa": float(df.iloc[0].get("Cassa", 0)),
                "EBITDA": float(df.iloc[0].get("EBITDA", 0)),
                "Flusso di cassa operativo": float(df.iloc[0].get("Flusso di cassa operativo", 0))
            }
        except Exception as e:
            debug_info["errore"] = f"Errore lettura Excel: {str(e)}"

    elif file_path.endswith(('.txt', '.md', '.csv')):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
                debug_info["estratto"] = text[:2000]
                data = extract_all_values_smart(text)
        except Exception as e:
            debug_info["errore"] = f"Errore apertura file testo: {str(e)}"

    else:
        debug_info["errore"] = f"Formato non supportato: {file_path}"

    return (data, debug_info) if return_debug else data

def calculate_kpis(data):
    ricavi = data.get("Ricavi", 0)
    costi = data.get("Costi", 0)
    utile = data.get("Utile Netto", 0)
    attivo = data.get("Totale Attivo", 1)
    pn = data.get("Patrimonio Netto", 1)
    debiti = data.get("Debiti Totali", 0)
    cassa = data.get("Cassa", 0)
    ebitda = data.get("EBITDA", 0)
    flusso = data.get("Flusso di cassa operativo", 0)

    kpis = {
        "Margine Operativo (%)": round((ricavi - costi) / ricavi * 100, 2) if ricavi else 0,
        "ROE (%)": round(utile / pn * 100, 2) if pn else 0,
        "ROA (%)": round(utile / attivo * 100, 2) if attivo else 0,
        "Ricavi / Attivo": round(ricavi / attivo, 2) if attivo else 0,
        "Indice di Efficienza (%)": round(utile / costi * 100, 2) if costi else 0,
        "Debt / Equity": round(debiti / pn, 2) if pn else 0,
        "Current Ratio": round(cassa / debiti, 2) if debiti else 0,
        "EBITDA Margin (%)": round(ebitda / ricavi * 100, 2) if ricavi else 0,
        "Cash Flow / Utile Netto": round(flusso / utile, 2) if utile else 0
    }
    return pd.DataFrame(list(kpis.items()), columns=["KPI", "Valore"])

def plot_kpis(df_kpis):
    fig = px.bar(df_kpis, x="KPI", y="Valore", title="KPI Finanziari Estesi", text="Valore")
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig.update_layout(yaxis_title="Valore", xaxis_title="", showlegend=False)
    return fig
