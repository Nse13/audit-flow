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
    pattern = r"(Revenue|Net Income|EBITDA|Total Assets|Equity|Total Debts|Operating Expenses|Cash Flow|Investments):\s*(?:EUR)?\s*([\d.,]+)"
    matches = re.findall(pattern, text, re.IGNORECASE)
    data = {}
    for key, value in matches:
        cleaned_value = value.replace(",", "").replace(".", "")
        try:
            data[key.strip()] = int(cleaned_value)
        except:
            data[key.strip()] = 0
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
        st.text_area("Contenuto", text, height=250)

        st.subheader("📊 Dati estratti")
        data = extract_numeric_data(text)
        st.json(data)

        if any(value > 0 for value in data.values()):
            df = pd.DataFrame([data])
            st.subheader("📈 KPI Calcolati")
            if "Revenue" in data and "Net Income" in data and data["Revenue"] != 0:
                df["Profit Margin (%)"] = round((data["Net Income"] / data["Revenue"]) * 100, 2)
            if "EBITDA" in data and "Total Assets" in data and data["Total Assets"] != 0:
                df["ROA (%)"] = round((data["EBITDA"] / data["Total Assets"]) * 100, 2)
            st.dataframe(df)

            # Grafico solo con i valori numerici rilevanti
            numeric_df = df.select_dtypes(include="number").T
            numeric_df.columns = ["Valore"]
            numeric_df["KPI"] = numeric_df.index
            fig = px.bar(numeric_df, x="Valore", y="KPI", orientation="h", title="📊 KPI principali")
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("💡 Raccomandazioni")
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