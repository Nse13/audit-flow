# --- utils.py ---
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
    for c in db.get(chiave, []):
        if c.get("testo") and c["testo"] in text:
            return c["valore"]
    return None






def smart_extract_value(keyword, synonyms, text, return_debug=False):
    candidates = []
    lines = text.split("\n")
    all_terms = [keyword.lower()] + [s.lower() for s in synonyms]

    for i, line in enumerate(lines):
        line_lower = line.lower()
        found_term = next((term for term in all_terms if term in line_lower), None)

        if not found_term:
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

            if "billion" in line_lower or "miliardi" in line_lower:
                val *= 1_000_000_000
            elif "million" in line_lower or "milioni" in line_lower:
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
            if any(x in line_lower for x in ["statement", "income", "balance"]): score += 2
            if "note" in line_lower: score -= 2
            if "cash flow" in line_lower: score += 1
            if "%" in line or "percent" in line_lower: score -= 1

            candidates.append({
                "term": found_term,
                "valore": val,
                "score": score,
                "riga": line
            })

    best = sorted(candidates, key=lambda x: x["score"], reverse=True)
    if return_debug:
        return best
    return best[0] if best else {"valore": 0.0, "score": 0, "riga": ""}








def extract_all_values_smart(text, return_debug=False):
    keywords_map = {
        # Conto economico
        "Ricavi": ["Totale ricavi", "Vendite", "Ricavi netti", "Revenue", "Proventi", "Net revenues", "Total revenues", "Revenues"],
        "Costi": ["Costi totali", "Spese", "Costi operativi", "Oneri", "Total expenses"],
        "Utile Netto": ["Risultato netto", "Utile dell'esercizio", "Risultato d'esercizio", "Profit", "Net income", "Net profit"],
        "EBITDA": ["EBITDA", "Margine operativo lordo"],
        "EBIT": ["EBIT", "Risultato operativo", "Operating income", "Operating profit", "Adjusted operating income", "AOI"],
        "Cash Flow Operativo": ["Cash Flow Operativo", "Operating cash flow", "Flusso di cassa operativo", "Net cash from operating activities"],

        # Stato patrimoniale
        "Totale Attivo": ["Totale attivo", "Attività totali", "Total Assets"],
        "Attivo Corrente": ["Attivo corrente", "Current assets"],
        "Patrimonio Netto": ["Capitale proprio", "Patrimonio netto", "Net Equity", "Total equity", "Equity"],
        "Debiti a Breve": ["Debiti a breve", "Current liabilities"],
        "Debiti a Lungo": ["Debiti a lungo", "Long-term debt", "Debiti finanziari a lungo termine"],
        "Cash Equivalents": ["Disponibilità liquide", "Cash and cash equivalents", "Liquidità"]
    }

    risultati = {}
    debug_righe = {}

    for key, synonyms in keywords_map.items():
        confermato = check_valori_confermati(text, key)
        if confermato is not None:
            risultati[key] = confermato
        else:
            estratto = smart_extract_value(key, synonyms, text, return_debug=return_debug)
            if return_debug:
                debug_righe[key] = estratto  # lista di righe candidate
                risultati[key] = estratto[0]["valore"] if estratto else 0.0
            else:
                risultati[key] = estratto["valore"]

    return (risultati, debug_righe) if return_debug else risultati



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

    elif file_path.endswith((".txt", ".md", ".csv")):
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

    else:
        estensione = os.path.splitext(file_path)[1]
        debug_info["errore"] = f"⚠️ Formato non supportato: {estensione if estensione else 'nessuna estensione rilevata'}"

    return (data, debug_info) if return_debug else data


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

        # Efficienza
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


def plot_kpis(df_kpis):
    fig = px.bar(
        df_kpis,
        x="KPI",
        y="Valore",
        title="📊 KPI Finanziari",
        text="Valore"
    )
    fig.update_traces(
        texttemplate='%{text:.2f}',
        textposition='outside'
    )
    fig.update_layout(
        yaxis_title="Valore",
        xaxis_title="",
        showlegend=False,
        height=600,
        margin=dict(l=20, r=20, t=50, b=100)
    )
    return fig

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_pdf_report(data, df_kpis, commento="", filename="report_auditflow.pdf"):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, height - 50, "📊 Audit Flow+ - Report Analisi Bilancio")

    c.setFont("Helvetica", 11)
    y = height - 80
    for k, v in data.items():
        c.drawString(40, y, f"{k}: {v:,.2f}")
        y -= 16
        if y < 60:
            c.showPage()
            y = height - 50

    y -= 20
    c.setFont("Helvetica-Bold", 13)
    c.drawString(40, y, "📈 KPI Calcolati")
    y -= 20
    c.setFont("Helvetica", 10)
    for _, row in df_kpis.iterrows():
        c.drawString(50, y, f"{row['KPI']}: {row['Valore']}")
        y -= 15
        if y < 60:
            c.showPage()
            y = height - 50

    if commento:
        y -= 30
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "🧠 Commento AuditLLM")
        y -= 20
        c.setFont("Helvetica", 9)
        for line in commento.split("\n"):
            c.drawString(50, y, line)
            y -= 13
            if y < 60:
                c.showPage()
                y = height - 50

    c.save()

def genera_commento_ai(data):
    import openai
    openai.api_key = os.environ.get("OPENAI_API_KEY")

    if not openai.api_key:
        return "⚠️ Nessuna API key trovata. Impossibile generare commento."

    prompt = f"""
Sei un revisore contabile esperto. Analizza i seguenti dati estratti da un bilancio e fornisci una breve valutazione finanziaria:

{json.dumps(data, indent=2)}

Concentrati su:
- Redditività
- Solidità patrimoniale
- Liquidità e rischio finanziario
- Eventuali segnali di allerta

Scrivi in modo professionale e sintetico.
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Sei un revisore esperto che redige commenti di audit."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=400
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Errore nella generazione del commento: {str(e)}"
