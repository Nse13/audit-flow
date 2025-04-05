import fitz  # PyMuPDF
import pandas as pd
import re
import plotly.express as px
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# =========================
# 1. Estrattore PDF avanzato
# =========================

def extract_financial_data(file_path, return_debug=False):
    debug_info = {}
    data = {}

    if file_path.endswith(".pdf"):
        try:
            text = ""
            with fitz.open(file_path) as doc:
                for page in doc:
                    text += page.get_text()
            debug_info["tipo_file"] = "PDF"
            debug_info["estratto"] = text[:1000]
            data = extract_all_values_smart(text)
        except Exception as e:
            return {"errore": f"Formato non supportato: {file_path}"}, debug_info

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

# =========================
# 2. Parser con scoring avanzato
# =========================

def smart_extract_value(keyword, synonyms, text):
    candidates = []
    lines = text.split("\n")
    all_terms = [keyword.lower()] + [s.lower() for s in synonyms]

    for i, line in enumerate(lines):
        clean_line = line.strip()
        line_lower = clean_line.lower()
        found_term = next((term for term in all_terms if term in line_lower), None)
        if not found_term:
            continue

        numbers = re.findall(r"[-+]?\d[\d.,]*", clean_line)
        for num_str in numbers:
            try:
                val = float(num_str.replace(".", "").replace(",", "."))
            except:
                continue

            score = 0

            # 🔍 Criteri multipli per accuratezza
            if keyword.lower() in line_lower:
                score += 3
            if found_term != keyword.lower():
                score += 2
            if sum(term in line_lower for term in all_terms) == 1:
                score += 1
            if abs(line_lower.find(found_term) - line_lower.find(num_str)) < 25:
                score += 2
            if "€" in clean_line or ".00" in num_str or ",00" in num_str:
                score += 1
            if 1_000 <= val <= 10_000_000_000:
                score += 2
            if i < 15 or i > len(lines) - 15:
                score += 1
            if ":" in clean_line or "\t" in clean_line:
                score += 1
            if "totale" in line_lower:
                score += 2
            if val < 0 and any(term in line_lower for term in ["costo", "perdita", "oneri"]):
                score += 1
            if re.search(r"\d{1,3}([.,]\d{3})+", num_str):
                score += 1
            if any(p in line_lower for p in ["mil", "mln", "mld"]):
                score += 1
            if num_str.endswith("0" * 3):
                score += 1
            if sum(term in text.lower() for term in all_terms) > 5:
                score -= 1

            candidates.append({
                "valore": val,
                "score": score,
                "riga": clean_line
            })

    best = sorted(candidates, key=lambda x: x["score"], reverse=True)
    return best[0] if best else {"valore": 0.0, "score": 0, "riga": ""}

def extract_all_values_smart(text):
    keywords_map = {
        "Ricavi": ["Totale ricavi", "Vendite", "Ricavi netti", "Proventi", "Revenue", "Total revenue"],
        "Costi": ["Costi totali", "Spese", "Costi operativi", "Oneri", "Expenses"],
        "Utile Netto": ["Risultato netto", "Utile dell'esercizio", "Risultato d'esercizio", "Net income"],
        "Totale Attivo": ["Totale attivo", "Attività totali", "Total assets"],
        "Patrimonio Netto": ["Capitale proprio", "Patrimonio netto", "PN", "Equity"]
    }

    results = {}
    for key, synonyms in keywords_map.items():
        estratto = smart_extract_value(key, synonyms, text)
        results[key] = estratto["valore"]
    return results

# =========================
# 3. Calcolo KPI
# =========================

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

# =========================
# 4. Grafico interattivo
# =========================

def plot_kpis(df_kpis):
    fig = px.bar(df_kpis, x="KPI", y="Valore", title="KPI Finanziari", text="Valore")
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig.update_layout(yaxis_title="Valore (%)", xaxis_title="", showlegend=False)
    return fig

# =========================
# 5. PDF Export
# =========================

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
