import fitz  # PyMuPDF
import pandas as pd
import plotly.express as px
import os
import json
import re
import io

# OCR setup
OCR_AVAILABLE = False
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    pass

# PDF Table Extraction
PDFPLUMBER_AVAILABLE = False
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    pass

# Word support
DOCX_AVAILABLE = False
try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    pass

# Apprendimento progressivo (valori confermati)
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
            if keyword.lower() in line_lower: score += 3
            if found_term != keyword.lower(): score += 2
            if sum(term in line_lower for term in all_terms) == 1: score += 1
            if abs(line_lower.find(found_term) - line_lower.find(num_str)) < 25: score += 2
            if "€" in line or ".00" in num_str or ",00" in num_str: score += 1
            if 1_000 <= val <= 100_000_000_000: score += 1
            if i < 10 or i > len(lines) - 10: score += 1
            if ":" in line or "\t" in line: score += 1
            if "totale" in line_lower: score += 2
            if val < 0 and any(x in line_lower for x in ["perdita", "costo", "oneri"]): score += 1
            if sum(term in text.lower() for term in all_terms) > 4: score -= 1
            if any(x in line_lower for x in ["2023", "2022", "2024"]): score -= 2
            if "consolidated" in line_lower: score += 1

            candidates.append({"term": found_term, "valore": val, "score": score, "riga": line})

    best = sorted(candidates, key=lambda x: x["score"], reverse=True)
    return best[0] if best else {"valore": 0.0, "score": 0, "riga": ""}
def estrai_testo_da_file(file_path):
    ext = file_path.lower()
    testo = ""

    if ext.endswith(".pdf") and PDFPLUMBER_AVAILABLE:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                testo += page.extract_text() or ""

    elif ext.endswith(".pdf") and not PDFPLUMBER_AVAILABLE:
        with fitz.open(file_path) as doc:
            for page in doc:
                t = page.get_text()
                if not t and OCR_AVAILABLE:
                    pix = page.get_pixmap()
                    img = Image.open(io.BytesIO(pix.tobytes()))
                    t = pytesseract.image_to_string(img, lang="ita")
                testo += t + "\n"

    elif ext.endswith((".xlsx", ".xls")):
        try:
            df = pd.read_excel(file_path)
            testo = "\n".join(" ".join(map(str, row)) for row in df.values)
        except Exception as e:
            testo = f"Errore lettura Excel: {e}"

    elif ext.endswith(".docx") and DOCX_AVAILABLE:
        try:
            doc = docx.Document(file_path)
            testo = "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            testo = f"Errore lettura Word: {e}"

    elif ext.endswith(".txt"):
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            testo = f.read()

    return testo.strip()

def extract_all_values_smart(text):
    keywords_map = {
        "Ricavi": ["Totale ricavi", "Vendite", "Ricavi netti", "Revenue", "Proventi", "Net revenues"],
        "Costi": ["Costi totali", "Spese", "Costi operativi", "Oneri", "Total expenses"],
        "Utile Netto": ["Risultato netto", "Utile dell'esercizio", "Risultato d'esercizio", "Profit", "Net income"],
        "Totale Attivo": ["Totale attivo", "Attività totali", "Total Assets"],
        "Patrimonio Netto": ["Capitale proprio", "Patrimonio netto", "Net Equity", "PN", "Total equity"],
        "Debiti": ["Liabilities", "Total liabilities", "Passivo", "Debiti totali"],
        "Disponibilità": ["Disponibilità liquide", "Cash and cash equivalents", "Liquidità"],
        "EBITDA": ["EBITDA", "Earnings Before Interest Taxes Depreciation"],
        "EBIT": ["EBIT", "Earnings Before Interest and Taxes"],
        "Interessi Passivi": ["Interest expense", "Oneri finanziari"],
        "Rimanenze": ["Inventories", "Rimanenze finali", "Magazzino"],
        "Crediti": ["Receivables", "Crediti", "Accounts receivable"],
        "Debiti Breve": ["Current liabilities", "Debiti a breve"],
        "Attivo Corrente": ["Current assets", "Attività correnti"]
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

    try:
        text = estrai_testo_da_file(file_path)
        debug_info["estratto"] = text[:2000]
        data = extract_all_values_smart(text)
    except Exception as e:
        debug_info["errore"] = str(e)

    return (data, debug_info) if return_debug else data
def calculate_kpis(data):
    ricavi = data.get("Ricavi", 0)
    costi = data.get("Costi", 0)
    utile = data.get("Utile Netto", 0)
    attivo = data.get("Totale Attivo", 1)
    pn = data.get("Patrimonio Netto", 1)
    debiti = data.get("Debiti", 0)
    disponibilita = data.get("Disponibilità", 0)
    ebitda = data.get("EBITDA", 0)
    ebit = data.get("EBIT", 0)
    interessi = data.get("Interessi Passivi", 1)
    crediti = data.get("Crediti", 1)
    rimanenze = data.get("Rimanenze", 1)
    debiti_breve = data.get("Debiti Breve", 1)
    attivo_corrente = data.get("Attivo Corrente", 1)

    kpis = {
        "Margine Operativo (%)": round((ricavi - costi) / ricavi * 100, 2) if ricavi else 0,
        "Return on Equity (ROE)": round(utile / pn * 100, 2) if pn else 0,
        "Return on Assets (ROA)": round(utile / attivo * 100, 2) if attivo else 0,
        "Rapporto Ricavi/Attivo": round(ricavi / attivo, 2) if attivo else 0,
        "Indice di Efficienza": round(utile / costi * 100, 2) if costi else 0,
        "Debt/Equity": round(debiti / pn, 2) if pn else 0,
        "Quick Ratio": round((disponibilita + crediti) / debiti_breve, 2) if debiti_breve else 0,
        "Current Ratio": round(attivo_corrente / debiti_breve, 2) if debiti_breve else 0,
        "EBITDA Margin": round(ebitda / ricavi * 100, 2) if ricavi else 0,
        "EBIT Margin": round(ebit / ricavi * 100, 2) if ricavi else 0,
        "Interest Coverage": round(ebit / interessi, 2) if interessi else 0,
        "Rotazione Crediti": round(ricavi / crediti, 2) if crediti else 0,
        "Rotazione Magazzino": round(costi / rimanenze, 2) if rimanenze else 0,
        "Capitale Proprio/Attivo": round(pn / attivo, 2) if attivo else 0,
        "Sustainable Growth (ROE x retention)": round((utile / ricavi) * (utile / pn) * 100, 2) if ricavi and pn else 0
    }

    return pd.DataFrame(list(kpis.items()), columns=["KPI", "Valore"])

def plot_kpis(df_kpis):
    fig = px.bar(df_kpis, x="KPI", y="Valore", title="KPI Finanziari Estesi", text="Valore")
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig.update_layout(yaxis_title="Valore", xaxis_title="", showlegend=False)
    return fig
