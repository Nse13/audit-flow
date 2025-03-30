
import streamlit as st
import pandas as pd
import plotly.express as px

# Modulo raccomandazioni importato
from app_auditflow_recommendation_engine import smart_recommendations

st.set_page_config(page_title="Audit Flow Pro+ Intelligent", layout="wide", page_icon="🧠")
st.image("logo_auditflow.png", width=300)
st.title("📊 Audit Flow Pro+ con Raccomandazioni Intelligenti")
st.write("Analisi di KPI finanziari con suggerimenti automatici intelligenti.")

uploaded_file = st.file_uploader("📂 Carica un file Excel o CSV", type=["xlsx", "xls", "csv"])

def calculate_kpi(row):
    kpi = {}
    try: kpi["ROE (%)"] = round(row["Net Income"] / row["Equity"] * 100, 2)
    except: pass
    try: kpi["Net Margin (%)"] = round(row["Net Income"] / row["Revenue"] * 100, 2)
    except: pass
    try: kpi["Debt to Equity"] = round(row["Total Debts"] / row["Equity"], 2)
    except: pass
    return kpi

if uploaded_file:
    df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith("xlsx") else pd.read_csv(uploaded_file)
    st.subheader("📄 Dati caricati")
    st.dataframe(df)

    if "Year" in df.columns:
        all_kpi = []
        for _, row in df.iterrows():
            kpi = calculate_kpi(row)
            kpi["Year"] = row["Year"]
            all_kpi.append(kpi)

        kpi_df = pd.DataFrame(all_kpi).set_index("Year")
        st.subheader("📈 KPI calcolati")
        st.dataframe(kpi_df)

        st.subheader("📉 Grafici KPI")
        for col in kpi_df.columns:
            fig = px.line(kpi_df, x=kpi_df.index, y=col, markers=True, title=col)
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("🧠 Raccomandazioni Intelligenti")
        for year, row in kpi_df.iterrows():
            with st.expander(f"Anno {year}"):
                recs = smart_recommendations(row)
                for r in recs:
                    st.markdown(f"- {r}")
    else:
        st.warning("⚠️ Aggiungi una colonna 'Year' per abilitare l'analisi multi-periodo.")
else:
    st.info("Carica un file Excel o CSV per iniziare.")
