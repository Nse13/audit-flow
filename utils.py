import fitz  # PyMuPDF
import pandas as pd
import plotly.express as px
import re

# ✅ SMART EXTRACT aggiornato
def smart_extract_value(keyword, synonyms, text):
    lines = text.split("\n")
    all_terms = [keyword.lower()] + [s.lower() for s in synonyms]
    candidates = []

    for i, line in enumerate(lines):
        line_clean = line.strip()
        line_lower = line_clean.lower()

        found_term = next((term for term in all_terms if term in line_lower), None)
        if not found_term:
            continue

        numbers = re.findall(r"[-+]?\d[\d.,]{1,}", line_clean)
        for num_str in numbers:
            try:
                val = float(num_str.replace(".", "").replace(",", "."))
            except:
                continue

            score = 0

            if keyword.lower() in line_lower:
                score += 3
            if found_term != keyword.lower():
                score += 2
            if sum(term in line_lower for term in all_terms) == 1:
                score += 1
            if abs(line_lower.find(found_term) - line_lower.find(num_str)) < 25:
                score += 2
            if any(u in line_lower for u in ["€", "mln", "milioni", "million"]):
                score += 3
            if 1_000 <= val <= 1_000_000_000:
                score += 1
            if i < 10 or i > len(lines) - 10:
                score += 1
            if ":" in line_lower or "\t" in line_lower:
                score += 1
            if "totale" in line_lower or "netto" in line_lower:
                score += 2
            if val < 0 and any(term in line_lower for term in ["costo", "perdita", "oneri"]):
                score += 1
            if sum(term in text.lower() for term in all_terms) > 4:
                score -= 1

            candidates.append({
                "term": found_term,
                "valore": val,
                "score": score,
                "riga": line_clean
            })

    best = sorted(candidates, key=lambda x: x["score"], reverse=True)
    return best[0] if best else {"valore": 0.0, "score": 0, "riga": ""}


# ✅ Dizionario sinonimi
def extract_all_values_smart(text):
    keywords_map = {
        "Ricavi": ["Totale ricavi", "Net revenues", "Ricavi netti", "Vendite", "Revenues"],
        "Costi": ["Costi totali", "Spese", "Costi operativi", "Oneri", "Total costs"],
        "Utile Netto": ["Risultato netto", "Utile dell'esercizio", "Net profit", "Net income"],
        "Totale Attivo": ["Totale attivo", "Total assets", "Attività totali"],
        "Patrimonio Netto": ["Capitale proprio", "Patrimonio netto", "Total equity", "Net equity"]
    }

    results = {}
    for key, synonyms in keywords_map.items():
        estratto = smart_extract_value(key, synonyms, text)
        results[key] = estratto["valore"]
    return results


# ✅ Estrazione da PDF
def extract_financial_data_from_pdf(file_path):
    risultati = {}
    righe_debug = []

    try:
        with fitz.open(file_path) as doc:
            text = ""
            for page in doc:
                text += page.get_text("text") + "\n"

            risultati = extract_all_values_smart(text)

    except Exception as e:
        return {}, {"errore apertura PDF": str(e)}

    return risultati, text[:2000]


# ✅ Funzione principale
def extract_financial_data(file_path, return_debug=False, use_gpt=False):
    data = {}
    debug_info = {}

    if file_path.endswith(".pdf"):
        data, raw = extract_financial_data_from_pdf(file_path)
        debug_info["tipo_file"] = "PDF"
        debug_info["estratto"] = raw
    elif file_path.endswith((".xlsx", ".xls")):
        try:
            df = pd.read_excel(file_path)
            debug_info["tipo_file"] = "EXCEL"
            debug_info["colonne"] = df.columns.tolist()
            data = {
                "Ricavi": float(df.iloc[0]["Ricavi"]),
                "Costi": float(df.iloc[0]["Costi"]),
                "Utile Netto": float(df.iloc[0]["Utile Netto"]),
                "Totale Attivo": float(df.iloc[0]["Totale Attivo"]),
                "Patrimonio Netto": float(df.iloc[0]["Patrimonio Netto"])
            }
        except Exception as e:
            debug_info["errore"] = str(e)
    else:
        debug_info["errore"] = f"Formato non supportato: {file_path}"

    return (data, debug_info) if return_debug else data


# ✅ KPI
def calculate_kpis(data):
    ricavi = data.get("Ricavi", 0)
    costi = data.get("Costi", 0)
    utile = data.get("Utile Netto", 0)
    attivo = data.get("Totale Attivo", 1)
    pn = data.get("Patrimonio Netto", 1)

    kpis = {
        "Margine Operativo (%)": round((ricavi - costi) / ricavi * 100, 2) if ricavi and costi else 0,
        "Return on Equity (ROE)": round(utile / pn * 100, 2) if pn else 0,
        "Return on Assets (ROA)": round(utile / attivo * 100, 2) if attivo else 0,
        "Rapporto Ricavi/Attivo": round(ricavi / attivo, 2) if attivo else 0,
        "Indice di Efficienza": round(utile / costi * 100, 2) if costi else 0
    }
    return pd.DataFrame(list(kpis.items()), columns=["KPI", "Valore"])


# ✅ Grafico KPI
def plot_kpis(df_kpis):
    fig = px.bar(df_kpis, x="KPI", y="Valore", title="KPI Finanziari", text="Valore")
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig.update_layout(yaxis_title="Valore (%)", xaxis_title="", showlegend=False)
    return fig
