import streamlit as st
import pandas as pd
import plotly.express as px
import re

st.set_page_config(
    page_title="Audit Flow Pro+",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Audit Flow Pro+")
st.subheader("Analisi finanziaria da PDF/Excel/CSV anche senza intelligenza artificiale")

uploaded_file = st.file_uploader("📎 Carica un bilancio PDF, Excel o CSV", type=["pdf", "csv", "xlsx"])

def extract_numeric_data(text):
    pattern = r"(Revenue|Net Income|EBITDA|Total Assets|Equity|Total Debts|Operating Expenses|Cash Flow|Investments):?\s*(?:EUR)?\s*([\d,.]+)"
    matches = re.findall(pattern, text, re.IGNORECASE)
    data = {}
    for key, value in matches:
        cleaned_value = value.replace(".", "").replace(",", ".")
        try:
            data[key.strip()] = float(cleaned_value)
        except:
            pass
    return data

def generate_recommendations(data):
    recs = []
    if data.get("Profit Margin (%)", 0) < 5:
        recs.append("🔍 Margine di profitto basso: valutare riduzione costi o aumento ricavi.")
    if data.get("ROA (%)", 0) < 5:
        recs.append("🏭 Basso ritorno sugli asset: migliorare efficienza operativa.")
    if data.get("EBITDA", 0) < 1_000_000:
        recs.append("📉 EBITDA contenuto: analizzare la sostenibilità della gestione caratteristica.")
    if not recs:
        recs.append("✅ Ottimo profilo finanziario: nessuna criticità rilevata.")
    return recs

if uploaded_file:
    if uploaded_file.name.endswith(".pdf"):
        import fitz  # PyMuPDF
        text = ""
        with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
        st.subheader("📄 Testo estratto")
        st.text(text)

        st.subheader("📊 Dati estratti")
        data = extract_numeric_data(text)
        st.json(data)

        if data:
            df = pd.DataFrame([data])
            st.subheader("📈 KPI Calcolati")
            if "Revenue" in data and "Net Income" in data:
                df["Profit Margin (%)"] = round((data["Net Income"] / data["Revenue"]) * 100, 2)
            if "EBITDA" in data and "Total Assets" in data:
                df["ROA (%)"] = round((data["EBITDA"] / data["Total Assets"]) * 100, 2)
            st.dataframe(df)

            # Plot KPI
            st.subheader("📊 Visualizzazione KPI")
            kpi_plot = df.drop(columns=["Cash Flow"]) if "Cash Flow" in df else df
            fig = px.bar(kpi_plot.T, orientation="h", labels={"index": "KPI", "value": "Valore (€)"}, title="KPI principali")
            st.plotly_chart(fig, use_container_width=True)

            # Raccomandazioni
            st.subheader("💡 Raccomandazioni automatiche")
            for rec in generate_recommendations(df.iloc[0].to_dict()):
                st.markdown(f"- {rec}")
        else:
            st.warning("⚠️ Nessun dato rilevato.")

    elif uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
        st.dataframe(df)
    elif uploaded_file.name.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
        st.dataframe(df)