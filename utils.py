# --- utils.py ---
import os
import io
import json
import re
import difflib
import fitz                      # PyMuPDF per lettura PDF
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# Supporto OCR
OCR_AVAILABLE = False
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    pass

# Database valori confermati (apprendimento progressivo)
CONFIRMATION_DB = "confermati.json"

def salva_valore_confermato(chiave, testo, valore):
    """Salva in modo persistente le correzioni manuali dell'utente."""
    if not os.path.exists(CONFIRMATION_DB):
        with open(CONFIRMATION_DB, "w") as f:
            json.dump({}, f)
    with open(CONFIRMATION_DB, "r") as f:
        db = json.load(f)
    if chiave not in db:
        db[chiave] = []
    db[chiave].append({"testo": testo, "valore": valore})
    with open(CONFIRMATION_DB, "w") as f:
        json.dump(db, f, indent=2)

def check_valori_confermati(text, chiave):
    """Controlla se nel testo è già stata confermata una coppia (chiave, testo)."""
    if not os.path.exists(CONFIRMATION_DB):
        return None
    with open(CONFIRMATION_DB, "r") as f:
        db = json.load(f)
    for entry in db.get(chiave, []):
        if entry["testo"] in text:
            return entry["valore"]
    return None

def smart_extract_value(keyword, synonyms, text, return_debug=False):
    """
    Estrae il valore numerico più probabile associato a 'keyword',
    usando una serie di punteggi basati su sinonimi, prossimità e formattazione.
    """
    candidates = []
    lines = text.split("\n")
    all_terms = [keyword.lower()] + [s.lower() for s in synonyms]

    for i, line in enumerate(lines):
        ll = line.lower()
        # Trovo se uno dei termini compare esattamente o quasi
        term_found = next((t for t in all_terms if t in ll), None)
        if not term_found:
            # tentativo fuzzy match
            for t in all_terms:
                if difflib.get_close_matches(t, [ll], cutoff=0.85):
                    term_found = t
                    break
        if not term_found:
            continue

        # Cerco numeri nella riga
        nums = re.findall(r"[-+]?\d[\d.,]+", line)
        for num in nums:
            try:
                val = float(num.replace(".", "").replace(",", "."))
            except:
                continue

            # Gestione milioni / miliardi
            if "billion" in ll or "miliardi" in ll:
                val *= 1_000_000_000
            elif "million" in ll or "milioni" in ll:
                val *= 1_000_000

            # Scoring lineare
            score = 0
            if keyword.lower() in ll:
                score += 4
            if term_found != keyword.lower():
                score += 2
            if ll.count(term_found) == 1:
                score += 1
            if abs(ll.find(term_found) - ll.find(num)) < 25:
                score += 2
            if "€" in line or ".00" in num or ",00" in num:
                score += 1
            if 1_000 <= val <= 100_000_000_000:
                score += 2
            if i < 10 or i > len(lines) - 10:
                score += 1
            if ":" in line or "\t" in line:
                score += 1
            if "totale" in ll:
                score += 2
            if val < 0 and any(x in ll for x in ["perdita", "costo"]):
                score += 1
            if any(x in ll for x in ["2023", "2022", "2024"]):
                score -= 3
            if "consolidated" in ll:
                score += 2
            if any(x in ll for x in ["statement", "income", "balance"]):
                score += 2
            if "note" in ll:
                score -= 2
            if "cash flow" in ll:
                score += 1
            if "%" in line or "percent" in ll:
                score -= 1

            candidates.append({
                "term": term_found,
                "valore": val,
                "score": score,
                "riga": line.strip()
            })

    best = sorted(candidates, key=lambda x: x["score"], reverse=True)
    if return_debug:
        return best
    return best[0] if best else {"valore": 0.0, "score": 0, "riga": ""}

def extract_all_values_smart(text, return_debug=False):
    """
    Applica smart_extract_value a un insieme di keyword di bilancio.
    Restituisce un dizionario chiave→valore e, in modalità debug, anche le righe candidate.
    """
    keywords_map = {
        "Ricavi": ["Totale ricavi", "Vendite", "Ricavi netti", "Revenue"],
        "Costi": ["Costi totali", "Spese", "Oneri", "Total expenses"],
        "Utile Netto": ["Risultato netto", "Net income", "Profit"],
        "EBITDA": ["EBITDA", "Margine operativo lordo"],
        "EBIT": ["EBIT", "Risultato operativo", "Operating income"],
        "Cash Flow Operativo": ["Flusso di cassa operativo", "Operating cash flow"],

        "Totale Attivo": ["Totale attivo", "Total assets"],
        "Attivo Corrente": ["Attivo corrente", "Current assets"],
        "Patrimonio Netto": ["Capitale proprio", "Net equity"],
        "Debiti a Breve": ["Debiti a breve", "Current liabilities"],
        "Debiti a Lungo": ["Debiti a lungo", "Long-term debt"],
        "Cash Equivalents": ["Disponibilità liquide", "Cash and cash equivalents"]
    }

    risultati = {}
    debug_righe = {}

    for key, syn in keywords_map.items():
        # se già confermato manualmente, lo usiamo
        confermato = check_valori_confermati(text, key)
        if confermato is not None:
            risultati[key] = confermato
            if return_debug:
                debug_righe[key] = []
        else:
            estr = smart_extract_value(key, syn, text, return_debug)
            if return_debug:
                debug_righe[key] = estr             # lista di candidati
                risultati[key] = estr[0]["valore"] if estr else 0.0
            else:
                risultati[key] = estr["valore"]

    if return_debug:
        return risultati, debug_righe
    return risultati

def extract_financial_data(file_path, return_debug=False):
    """
    Estrae testo dal file (PDF/Excel/txt/docx), poi chiama extract_all_values_smart.
    Se return_debug=True, ritorna (data, debug_info).
    """
    debug_info = {}
    data = {}

    # PDF
    if file_path.lower().endswith(".pdf"):
        text = ""
        try:
            doc = fitz.open(file_path)
            for page in doc:
                pagetext = page.get_text()
                if not pagetext and OCR_AVAILABLE:
                    pix = page.get_pixmap()
                    img = Image.open(io.BytesIO(pix.tobytes()))
                    pagetext = pytesseract.image_to_string(img, lang="ita")
                text += pagetext + "\n"
            doc.close()
        except Exception as e:
            debug_info["errore"] = f"Errore apertura PDF: {e}"
            return (data, debug_info) if return_debug else data

        debug_info["estratto"] = text[:2000]
        data, debug_righe = extract_all_values_smart(text, return_debug=True)
        debug_info["righe_candidate"] = debug_righe

    # Excel (.xlsx, .xls)
    elif file_path.lower().endswith((".xlsx", ".xls")):
        try:
            df = pd.read_excel(file_path)
            # prendo la prima riga e i nomi di colonna corrispondenti
            row = df.iloc[0]
            data = {
                "Ricavi": row.get("Ricavi", 0),
                "Costi": row.get("Costi", 0),
                "Utile Netto": row.get("Utile Netto", 0),
                "Totale Attivo": row.get("Totale Attivo", 0),
                "Patrimonio Netto": row.get("Patrimonio Netto", 0)
            }
        except Exception as e:
            debug_info["errore"] = f"Errore lettura Excel: {e}"

    # Testo semplice (.txt, .md, .csv)
    elif file_path.lower().endswith((".txt", ".md", ".csv")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            debug_info["estratto"] = text[:2000]
            data, debug_righe = extract_all_values_smart(text, return_debug=True)
            debug_info["righe_candidate"] = debug_righe
        except Exception as e:
            debug_info["errore"] = f"Errore apertura testo: {e}"

    else:
        debug_info["errore"] = f"Formato non supportato: {file_path}"

    return (data, debug_info) if return_debug else data

def calculate_kpis(data):
    """
    Calcola un set completo di KPI redditività, liquidità, leva, efficienza, cash flow.
    Ritorna un DataFrame con colonne ['KPI','Valore'].
    """
    ricavi      = data.get("Ricavi", 0)
    costi       = data.get("Costi", 0)
    utile       = data.get("Utile Netto", 0)
    attivo      = data.get("Totale Attivo", 1)
    pn          = data.get("Patrimonio Netto", 1)
    deb_brevi   = data.get("Debiti a Breve", 0)
    deb_lunghi  = data.get("Debiti a Lungo", 0)
    att_corr    = data.get("Attivo Corrente", 0)
    cf_operativo= data.get("Cash Flow Operativo", 0)
    cash_eq     = data.get("Cash Equivalents", 0)
    ebitda      = data.get("EBITDA", 0)
    ebit        = data.get("EBIT", 0)
    oneri_fin   = data.get("Oneri Finanziari", 1)

    kpis = {
        # Redditività
        "Margine Operativo (%)": round((ricavi - costi)/ricavi*100, 2) if ricavi else 0,
        "EBITDA Margin (%)":     round(ebitda/ricavi*100, 2)    if ricavi else 0,
        "EBIT Margin (%)":       round(ebit/ricavi*100, 2)      if ricavi else 0,
        "Return on Equity (ROE)":round(utile/pn*100, 2)         if pn     else 0,
        "Return on Assets (ROA)":round(utile/attivo*100, 2)     if attivo else 0,

        # Liquidità
        "Current Ratio":         round(att_corr/deb_brevi, 2)    if deb_brevi else 0,
        "Cash Ratio":            round(cash_eq/deb_brevi, 2)     if deb_brevi else 0,

        # Leva finanziaria
        "Debt to Equity":        round((deb_brevi+deb_lunghi)/pn, 2) if pn else 0,
        "Debt to Assets":        round((deb_brevi+deb_lunghi)/attivo, 2) if attivo else 0,

        # Efficienza
        "Indice di Efficienza (%)": round(utile/costi*100, 2)    if costi else 0,
        "Ricavi / Totale Attivo":    round(ricavi/attivo, 2)     if attivo else 0,
        "Copertura Interessi":       round(ebit/oneri_fin, 2)    if oneri_fin else 0,

        # Cash Flow
        "Cash Flow su Utile Netto":  round(cf_operativo/utile, 2) if utile else 0,
        "Cash Flow su Ricavi":       round(cf_operativo/ricavi,2) if ricavi else 0,
        "Cash Flow Margin (%)":      round(cf_operativo/ricavi*100, 2) if ricavi else 0,

        # Indicatori personalizzati
        "Capacità di autofinanziamento": round((utile+cf_operativo)/ricavi*100, 2) if ricavi else 0,
        "Indice di solidità patrimoniale": round(pn/attivo, 2) if attivo else 0,
        "Margine di struttura": round(pn - deb_lunghi, 2)
    }

    return pd.DataFrame(list(kpis.items()), columns=["KPI", "Valore"])

def plot_kpis(df_kpis):
    """
    Separa KPI percentuali da quelli assoluti e
    genera due grafici Plotly (bar chart).
    """
    # Filtri
    df_pct = df_kpis[df_kpis["KPI"].str.contains("%")]
    df_abs = df_kpis[~df_kpis["KPI"].str.contains("%")]

    # Grafico percentuali
    if not df_pct.empty:
        fig_pct = px.bar(
            df_pct, x="KPI", y="Valore",
            title="📊 KPI Percentuali",
            text="Valore"
        )
        fig_pct.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
        fig_pct.update_layout(yaxis_title="Percentuale", showlegend=False,
                              height=400, margin=dict(l=20,r=20,t=40,b=80))
    else:
        fig_pct = go.Figure()
        fig_pct.update_layout(title="📊 Nessun KPI Percentuale disponibile")

    # Grafico assoluti
    if not df_abs.empty:
        fig_abs = px.bar(
            df_abs, x="KPI", y="Valore",
            title="📊 KPI Valori Assoluti",
            text="Valore"
        )
        fig_abs.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        fig_abs.update_layout(yaxis_title="Valore", showlegend=False,
                              height=400, margin=dict(l=20,r=20,t=40,b=80))
    else:
        fig_abs = go.Figure()
        fig_abs.update_layout(title="📊 Nessun KPI Assoluto disponibile")

    return fig_pct, fig_abs

def generate_pdf_report(data, df_kpis, commento="", filename="report_auditflow.pdf"):
    """
    Genera un PDF con i dati estratti, i KPI e il commento AI.
    """
    c = canvas.Canvas(filename, pagesize=A4)
    w, h = A4

    # Titolo
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, h-50, "📊 Audit Flow+ - Report Analisi Bilancio")

    # Dati numerici
    c.setFont("Helvetica", 10)
    y = h - 80
    for k, v in data.items():
        txt = f"{k}: {v:,.2f}% " if "%" in k else f"{k}: {v:,.2f}"
        c.drawString(40, y, txt)
        y -= 14
        if y < 60:
            c.showPage()
            y = h - 50

    # KPI
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "📈 KPI Calcolati")
    y -= 16
    c.setFont("Helvetica", 9)
    for _, row in df_kpis.iterrows():
        txt = f"{row['KPI']}: {row['Valore']:,.2f}% " if "%" in row["KPI"] else f"{row['KPI']}: {row['Valore']:,.2f}"
        c.drawString(50, y, txt)
        y -= 12
        if y < 60:
            c.showPage()
            y = h - 50

    # Commento AI
    if commento:
        y -= 20
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "🧠 Commento AuditLLM")
        y -= 14
        c.setFont("Helvetica", 9)
        for line in commento.split("\n"):
            c.drawString(50, y, line)
            y -= 12
            if y < 60:
                c.showPage()
                y = h - 50

    c.save()

def genera_commento_ai(data):
    """
    Genera un breve commento AI utilizzando OpenAI GPT.
    """
    try:
        import openai
        openai.api_key = os.getenv("OPENAI_API_KEY", "")
    except:
        return "⚠️ Libreria openai non trovata."

    if not openai.api_key:
        return "⚠️ Nessuna API key impostata per OpenAI."

    prompt = (
        "Sei un revisore contabile esperto. Analizza i seguenti dati estratti da un bilancio:\n"
        f"{json.dumps(data, indent=2)}\n\n"
        "Fornisci un breve commento su:\n"
        "- Redditività\n"
        "- Solidità patrimoniale\n"
        "- Liquidità e rischio finanziario\n"
        "- Segnali di allerta"
    )

    try:
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Sei un esperto revisore contabile."},
                {"role": "user",   "content": prompt}
            ],
            temperature=0.3,
            max_tokens=350
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        return f"Errore generazione commento AI: {e}"
