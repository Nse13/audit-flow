
import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import re
from fpdf import FPDF
import openai

# CONFIGURAZIONE STREAMLIT
st.set_page_config(page_title="Audit Flow", layout="wide")
st.title("📘 Audit Flow")
st.subheader("Smart Financial Analysis")
st.markdown("---")

# SIDEBAR UPLOAD
st.sidebar.header("📂 Carica un documento")
file = st.sidebar.file_uploader("Scegli un file Excel o PDF", type=["xlsx", "xls", "pdf"])

# FUNZIONE ESTRAZIONE TESTO DA PDF
def estrai_testo_da_pdf(uploaded_file):
    testo = ""
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        for page in doc:
            testo += page.get_text()
    return testo

# FUNZIONE ESTRAZIONE DATI DA TESTO
def estrai_valori_finanziari(testo):
    pattern = r"(?i)(RICAVI TOTALI|COSTI OPERATIVI|UTILE NETTO|EBITDA|FLUSSO DI CASSA OPERATIVO|DEBITI VERSO BANCHE|CREDITI COMMERCIALI|PATRIMONIO NETTO|TOTALE ATTIVO):\s*EUR?\s*([\d\.]+)"
    matches = re.findall(pattern, testo)
    dati = {k.upper(): float(v.replace(".", "")) for k, v in matches}
    return dati

# FUNZIONE CALCOLO KPI
def calcola_kpi(dati):
    try:
        ricavi = dati.get("RICAVI TOTALI", 0)
        utile = dati.get("UTILE NETTO", 0)
        cash = dati.get("FLUSSO DI CASSA OPERATIVO", 0)
        patrimonio = dati.get("PATRIMONIO NETTO", 0)
        debiti = dati.get("DEBITI VERSO BANCHE", 0)

        return {
            "Margine Utile Netto (%)": round((utile / ricavi) * 100, 2) if ricavi else None,
            "Cash Flow / Utile (%)": round((cash / utile) * 100, 2) if utile else None,
            "Debiti / Patrimonio (%)": round((debiti / patrimonio) * 100, 2) if patrimonio else None
        }
    except:
        return {}

# FUNZIONE COMMENTO GPT (mock temporaneo)
def commento_gpt(dati, kpi):
    ricavi = dati.get("RICAVI TOTALI", 0)
    utile = dati.get("UTILE NETTO", 0)
    rischio = "moderato nella riscossione dei crediti" if "CREDITI COMMERCIALI" in dati else "nessun rischio evidente"
    return (
        f"Nel 2024 l'azienda ha registrato ricavi pari a EUR {ricavi:,.0f} e un utile netto di EUR {utile:,.0f}. "
        f"Il margine netto risulta del {kpi.get('Margine Utile Netto (%)', 'N/A')}%. "
        f"Il cash flow operativo copre il {kpi.get('Cash Flow / Utile (%)', 'N/A')}% dell'utile. "
        f"Il rapporto Debiti/Patrimonio è pari a {kpi.get('Debiti / Patrimonio (%)', 'N/A')}%. "
        f"Si segnala un rischio {rischio}."
    )

# FUNZIONE PER GENERARE REPORT PDF
def genera_report_pdf(dati, kpi, commento):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Audit Flow - Report Analisi Bilancio", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.ln(10)

    pdf.cell(0, 10, "📌 Valori Finanziari Estratti:", ln=True)
    for k, v in dati.items():
        pdf.cell(0, 10, f"- {k.title().replace('_', ' ')}: EUR {v:,.0f}", ln=True)

    pdf.ln(10)
    pdf.cell(0, 10, "📊 Indicatori KPI Calcolati:", ln=True)
    for k, v in kpi.items():
        pdf.cell(0, 10, f"- {k}: {v}%", ln=True)

    pdf.ln(10)
    pdf.multi_cell(0, 10, f"🧠 Commento AI:
{commento}")
    path = "/mnt/data/AuditFlow_Report.pdf"
    pdf.output(path)
    return path

# MAIN LOGIC
if file:
    if file.type == "application/pdf":
        testo = estrai_testo_da_pdf(file)
        st.subheader("📄 Testo estratto dal PDF")
        st.text_area("Contenuto del bilancio", testo, height=300)

        st.subheader("📥 Analisi automatica")
        dati = estrai_valori_finanziari(testo)
        kpi = calcola_kpi(dati)
        commento = commento_gpt(dati, kpi)

        st.write("📌 **Valori finanziari estratti:**")
        st.json(dati)
        st.write("📊 **KPI calcolati:**")
        st.json(kpi)
        st.write("🧠 **Commento AI:**")
        st.success(commento)

        report = genera_report_pdf(dati, kpi, commento)
        with open(report, "rb") as f:
            st.download_button("📄 Scarica report PDF", f, file_name="AuditFlow_Report.pdf")
    else:
        st.warning("Carica un file PDF per l'analisi automatica.")
