import fitz  # PyMuPDF
import pandas as pd
import plotly.express as px
import os
import json
import re
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer

# OCR
OCR_AVAILABLE = False
try:
    import pytesseract
    from PIL import Image
    import io
    OCR_AVAILABLE = True
except ImportError:
    pass

# pdfplumber
PDFPLUMBER_AVAILABLE = False
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    pass

# === Apprendimento progressivo ===
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
        if isinstance(c, dict) and c.get("testo") and c["testo"] in text:
            return c["valore"]
    return None
# === ML semplificato ===
ML_MODEL = RandomForestClassifier(n_estimators=10, random_state=42)
ML_VECTOR = CountVectorizer()
ML_TRAINED = False

def train_ml_model(samples):
    global ML_MODEL, ML_VECTOR, ML_TRAINED
    texts = [s['text'] for s in samples]
    labels = [s['label'] for s in samples]
    X = ML_VECTOR.fit_transform(texts)
    ML_MODEL.fit(X, labels)
    ML_TRAINED = True

def ml_predict(text):
    if not ML_TRAINED:
        return 0
    X = ML_VECTOR.transform([text])
    return ML_MODEL.predict(X)[0]

# === Estrazione avanzata ===
def smart_extract_value(keyword, synonyms, text):
    candidates = []
    lines = text.split("\n")
    all_terms = [keyword.lower()] + [s.lower() for s in synonyms]

    for i, line in enumerate(lines):
        block = " ".join(lines[max(0, i-2):i+3]).lower()
        found_term = next((term for term in all_terms if term in block), None)
        if not found_term:
            continue

        numbers = re.findall(r"[-+]?\d[\d.,]+", block)
        for num_str in numbers:
            try:
                val = float(num_str.replace(".", "").replace(",", "."))
            except:
                continue

            # Rileva unità (milioni/migliaia) nei primi 25 heading
            multiplier = 1
            header_text = " ".join(lines[:25]).lower()
            if "million" in header_text or "milioni" in header_text:
                multiplier = 1_000_000
            elif "thousand" in header_text or "migliaia" in header_text:
                multiplier = 1_000
            val *= multiplier

            score = 0
            if keyword.lower() in block: score += 5
            if found_term != keyword.lower(): score += 2
            if sum(term in block for term in all_terms) == 1: score += 1
            if abs(block.find(found_term) - block.find(num_str)) < 25: score += 2
            if any(x in block for x in ["€", "$", "%", ".00", ",00"]): score += 1
            if 1_000 <= val <= 1_000_000_000_000: score += 2
            if i < 15 or i > len(lines) - 15: score += 1
            if any(x in line for x in [":", "\t", "........"]): score += 2
            if "totale" in block: score += 2
            if val < 0 and any(x in block for x in ["perdita", "loss", "negativo"]): score += 1
            if any(x in block for x in ["2023", "2022", "2024", "anno"]): score -= 3
            if len(num_str) <= 4 and val < 2100: score -= 2
            if "consolidated" in block or "statement of" in block: score += 2
            if block.count(" ") < 3: score -= 2
            if len(block) > 250: score -= 2
            if re.search(r"^\d{4}$", num_str): score -= 3

            # 🧠 Applica ML se disponibile
            if ML_TRAINED and ml_predict(line) == 1:
                score += 3

            candidates.append({
                "term": found_term,
                "valore": val,
                "score": score,
                "riga": line
            })

    best = sorted(candidates, key=lambda x: x["score"], reverse=True)
    return best[0] if best else {"valore": 0.0, "score": 0, "riga": ""}
# === Estrazione principale ===
def extract_financial_data(file_path, return_debug=False):
    debug_info = {}
    data = {}

    text = ""

    # 📘 Word
    if file_path.endswith(".docx"):
        try:
            import docx
            doc = docx.Document(file_path)
            text = "\n".join([p.text for p in doc.paragraphs])
            debug_info["tipo_file"] = "WORD"
        except Exception as e:
            debug_info["errore"] = f"Errore lettura DOCX: {str(e)}"
            return (data, debug_info) if return_debug else data

    # 📄 TXT
    elif file_path.endswith(".txt"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            debug_info["tipo_file"] = "TXT"
        except Exception as e:
            debug_info["errore"] = f"Errore lettura TXT: {str(e)}"
            return (data, debug_info) if return_debug else data

    # 🧾 EXCEL
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
            debug_info["tipo_file"] = "EXCEL"
            debug_info["colonne"] = df.columns.tolist()
            return (data, debug_info) if return_debug else data
        except Exception as e:
            debug_info["errore"] = f"Errore lettura Excel: {str(e)}"
            return (data, debug_info) if return_debug else data

    # 📑 PDF
    elif file_path.endswith(".pdf"):
        if PDFPLUMBER_AVAILABLE:
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text() or ""
                        tables = page.extract_tables()
                        for table in tables:
                            for row in table:
                                if row:
                                    text += "\n" + " ".join([cell or "" for cell in row])
                debug_info["tipo_file"] = "PDF (plumber)"
            except Exception as e:
                debug_info["errore"] = f"Errore pdfplumber: {str(e)}"

        if not text:
            try:
                with fitz.open(file_path) as doc:
                    for page in doc:
                        t = page.get_text()
                        if not t and OCR_AVAILABLE:
                            pix = page.get_pixmap()
                            img = Image.open(io.BytesIO(pix.tobytes()))
                            t = pytesseract.image_to_string(img, lang="ita")
                        text += t + "\n"
                debug_info["tipo_file"] = "PDF (fitz)"
            except Exception as e:
                debug_info["errore"] = f"Errore apertura PDF: {str(e)}"
                return (data, debug_info) if return_debug else data

    # ❌ Altro formato non supportato
    else:
        debug_info["errore"] = f"Formato non supportato: {file_path}"
        return (data, debug_info) if return_debug else data

    # 🧠 Estrazione dei dati con sistema smart
    debug_info["estratto"] = text[:2000]
    data = extract_all_values_smart(text)
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

# === Grafico KPI ===
def plot_kpis(df_kpis):
    fig = px.bar(df_kpis, x="KPI", y="Valore", title="KPI Finanziari", text="Valore")
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig.update_layout(yaxis_title="Valore (%)", xaxis_title="", showlegend=False)
    return fig
