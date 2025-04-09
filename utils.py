import fitz  # PyMuPDF
import pandas as pd
import plotly.express as px
import os
import json
import re
import difflib

# OCR support
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
            # Fuzzy fallback: trova il termine più simile
            for term in all_terms:
                match = difflib.get_close_matches(term, [line_lower], cutoff=0.85)
                if match:
                    found_term = term
                    break
        if not found_term:
            continue

        numbers = re.findall(r"[-+]?\d[\d.,]+", line)
        for num_str in numbers:
            try:
                val = float(num_str.replace(".", "").replace(",", "."))
            except:
                continue

            # Conversione in milioni
            if "million" in line_lower or "milioni" in line_lower:
                val *= 1_000_000

            score = 0
            if keyword.lower() in line_lower: score += 4
            if found_term != keyword.lower(): score += 2
            if sum(term in line_lower for term in all_terms) == 1: score += 1
            if abs(line_lower.find(found_term) - line_lower.find(num_str)) < 25: score += 2
            if "€" in line or ".00" in num_str or ",00" in num_str: score += 1
            if 1_000 <= val <= 100_000_000_000: score += 2
            if i < 10 or i > len(lines) - 10: score += 1
            if ":" in line or "\t" in line: score += 1
            if "totale" in line_lower: score += 2
            if val < 0 and any(x in line_lower for x in ["perdita", "costo"]): score += 1
            if any(x in line_lower for x in ["2023", "2022", "2024"]): score -= 3
            if "consolidated" in line_lower: score += 2
            if "statement" in line_lower or "income" in line_lower or "balance" in line_lower: score += 2
            if "note" in line_lower: score -= 2
            if "cash flow" in line_lower: score += 1
            if "%" in line or "percent" in line_lower: score -= 1  # evitare percentuali errate

            candidates.append({
                "term": found_term,
                "valore": val,
                "score": score,
                "riga": line
            })

    best = sorted(candidates, key=lambda x: x["score"], reverse=True)
    return best[0] if best else {"valore": 0.0, "score": 0, "riga": ""}
elif file_path.endswith(('.txt', '.md', '.csv')):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
            debug_info["estratto"] = text[:2000]
            data = extract_all_values_smart(text)
    except Exception as e:
        debug_info["errore"] = f"Errore apertura file testo: {str(e)}"

elif file_path.endswith(".docx"):
    try:
        import docx
        doc = docx.Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        debug_info["estratto"] = text[:2000]
        data = extract_all_values_smart(text)
    except Exception as e:
        debug_info["errore"] = f"Errore lettura Word: {str(e)}"
def calculate_kpis(data):
    ricavi = data.get("Ricavi", 0)
    costi = data.get("Costi", 0)
    utile = data.get("Utile Netto", 0)
    attivo = data.get("Totale Attivo", 1)
    pn = data.get("Patrimonio Netto", 1)
    debiti_brevi = data.get("Debiti a Breve", 0)
    debiti_lunghi = data.get("Debiti a Lungo", 0)
    attivo_corrente = data.get("Attivo Corrente", 0)
    cash_flow = data.get("Cash Flow Operativo", 0)
    cash_equivalents = data.get("Cash Equivalents", 0)
    ebitda = data.get("EBITDA", 0)
    ebit = data.get("EBIT", 0)
    oneri_fin = data.get("Oneri Finanziari", 1)
    proventi_fin = data.get("Proventi Finanziari", 0)

    kpis = {
        # Redditività
        "Margine Operativo (%)": round((ricavi - costi) / ricavi * 100, 2) if ricavi else 0,
        "EBITDA Margin (%)": round(ebitda / ricavi * 100, 2) if ricavi else 0,
        "EBIT Margin (%)": round(ebit / ricavi * 100, 2) if ricavi else 0,
        "Return on Equity (ROE)": round(utile / pn * 100, 2) if pn else 0,
        "Return on Assets (ROA)": round(utile / attivo * 100, 2) if attivo else 0,

        # Liquidità e solvibilità
        "Current Ratio": round(attivo_corrente / debiti_brevi, 2) if debiti_brevi else 0,
        "Cash Ratio": round(cash_equivalents / debiti_brevi, 2) if debiti_brevi else 0,

        # Leva finanziaria
        "Debt to Equity": round((debiti_brevi + debiti_lunghi) / pn, 2) if pn else 0,
        "Debt to Assets": round((debiti_brevi + debiti_lunghi) / attivo, 2) if attivo else 0,

        # Efficienza e performance
        "Indice di Efficienza (%)": round(utile / costi * 100, 2) if costi else 0,
        "Ricavi / Totale Attivo": round(ricavi / attivo, 2) if attivo else 0,
        "Copertura Interessi": round(ebit / oneri_fin, 2) if oneri_fin else 0,

        # Cash Flow
        "Cash Flow su Utile Netto": round(cash_flow / utile, 2) if utile else 0,
        "Cash Flow su Ricavi": round(cash_flow / ricavi, 2) if ricavi else 0,
        "Cash Flow Margin (%)": round(cash_flow / ricavi * 100, 2) if ricavi else 0,

        # Indicatori personalizzati
        "Capacità di autofinanziamento": round((utile + cash_flow) / ricavi * 100, 2) if ricavi else 0,
        "Indice di solidità patrimoniale": round(pn / attivo, 2) if attivo else 0,
        "Margine di struttura": round(pn - debiti_lunghi, 2)
    }

    return pd.DataFrame(list(kpis.items()), columns=["KPI", "Valore"])
# === KPI Chart ===
def plot_kpis(df_kpis):
    fig = px.bar(df_kpis, x="KPI", y="Valore", title="KPI Finanziari", text="Valore")
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig.update_layout(
        yaxis_title="Valore",
        xaxis_title="",
        showlegend=False,
        height=600
    )
    return fig

# === Report PDF ===
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_pdf_report(data, df_kpis, commento="", filename="report_auditflow.pdf"):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, height - 50, "Audit Flow+ - Report Analisi Bilancio")

    c.setFont("Helvetica", 11)
    y = height - 80
    for k, v in data.items():
        c.drawString(40, y, f"{k}: {v:,.2f}")
        y -= 16

    y -= 20
    c.setFont("Helvetica-Bold", 13)
    c.drawString(40, y, "KPI Calcolati")
    y -= 20
    c.setFont("Helvetica", 10)
    for _, row in df_kpis.iterrows():
        c.drawString(50, y, f"{row['KPI']}: {row['Valore']}")
        y -= 15
        if y < 50:
            c.showPage()
            y = height - 50

    if commento:
        y -= 30
        c.setFont("Helvetica
