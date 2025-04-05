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

# === Apprendimento Progressivo ===
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
        if c["testo"] in text:
            return c["valore"]
    return None

# === Estrazione Migliorata ===
def smart_extract_value(keyword, synonyms, text):
    candidates = []
    lines = text.split("\n")
    all_terms = [keyword.lower()] + [s.lower() for s in synonyms]

    for i, line in enumerate(lines):
        line_lower = line.lower()
        if len(line.split()) < 2:
            continue  # riga troppo breve

        found_term = next((term for term in all_terms if term in line_lower), None)
        if not found_term:
            continue

        numbers = re.findall(r"[-+]?\d[\d.,]+", line)
        for num_str in numbers:
            try:
                val = float(num_str.replace(".", "").replace(",", "."))
            except:
                continue

            score = 0
            if keyword.lower() in line_lower: score += 3
            if found_term != keyword.lower(): score += 2
            if sum(term in line_lower for term in all_terms) == 1: score += 1
            if abs(line_lower.find(found_term) - line_lower.find(num_str)) < 25: score += 2
            if "€" in line or ".00" in num_str or ",00" in num_str: score += 1
            if re.search(r"\d{1,3}[\.,]\d{3}", num_str): score += 2
            if any(w in line_lower for w in ["milioni", "migliaia", "euro", "€"]): score += 2
            if 1_000 <= val <= 1_000_000_000_000: score += 1
            if i < 10 or i > len(lines) - 10: score += 1
            if ":" in line or "\t" in line: score += 1
            if "totale" in line_lower: score += 2
            if val < 0 and any(x in line_lower for x in ["perdita", "costo"]): score += 1
            if sum(term in text.lower() for term in all_terms) > 4: score -= 1
            if 1900 <= val <= 2100: score -= 3  # penalità per anni

            candidates.append({"term": found_term, "valore": val, "score": score, "riga": line})

    best = sorted(candidates, key=lambda x: x["score"], reverse=True)
    return best[0] if best else {"valore": 0.0, "score": 0, "riga": ""}

def extract_all_values_smart(text):
    keywords_map = {
        "Ricavi": ["Totale ricavi", "Vendite", "Ricavi netti", "Revenue", "Proventi"],
        "Costi": ["Costi totali", "Spese", "Costi operativi", "Oneri"],
        "Utile Netto": ["Risultato netto", "Utile dell'esercizio", "Risultato d'esercizio", "Profit"],
        "Totale Attivo": ["Totale attivo", "Attività totali", "Total Assets"],
        "Patrimonio Netto": ["Capitale proprio", "Patrimonio netto", "Net Equity", "PN"]
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

# === Estrazione Principale ===
def extract_financial_data(file_path, return_debug=False, use_llm=False):
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

    elif file_path.endswith((".xlsx", ".xls")):
        try:
            df = pd.read_excel(file_path)
            data = {
                "Ricavi": float(df.iloc[0].get("Ricavi", 0)),
                "Costi": float(df.iloc[0].get("Costi", 0)),
                "Utile Netto": float(df.iloc[0].get("Utile Netto", 0)),
                "Totale Attivo": float(df.iloc[0].get("Totale Attivo", 0)),
                "Patrimonio Netto": float(df.iloc[0].get("Patrimonio Netto", 0))
            }
        except Exception as e:
            debug_info["errore"] = f"Errore lettura Excel: {str(e)}"

    else:
        debug_info["errore"] = f"Formato non supportato: {file_path}"

    return (data, debug_info) if return_debug else data

# === KPI ===
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

# === Grafico ===
def plot_kpis(df_kpis):
    fig = px.bar(df_kpis, x="KPI", y="Valore", title="KPI Finanziari", text="Valore")
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig.update_layout(yaxis_title="Valore (%)", xaxis_title="", showlegend=False)
    return fig
