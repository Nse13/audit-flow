# utils.py
import fitz  # PyMuPDF
import pandas as pd
import plotly.express as px
from openai import OpenAI
import json
import streamlit as st
import re

# Estrazione dati finanziari da PDF, Excel, CSV
def extract_financial_data(uploaded_file):
    data = {}
    if uploaded_file.name.endswith('.pdf'):
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        text = " ".join(page.get_text() for page in doc)
    elif uploaded_file.name.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(uploaded_file)
        text = df.to_string()
    elif uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
        text = df.to_string()
    else:
        text = uploaded_file.read().decode('utf-8')

    # Regex avanzate per un'ampia gamma di valori finanziari
    patterns = {
        "Revenue": r"(Revenue|Ricavi)[^\d]{0,10}([\d.,]+)",
        "Net Income": r"(Net Income|Utile Netto)[^\d]{0,10}([\d.,]+)",
        "EBITDA": r"EBITDA[^\d]{0,10}([\d.,]+)",
        "Total Assets": r"(Total Assets|Attività Totali)[^\d]{0,10}([\d.,]+)",
        "Equity": r"(Equity|Patrimonio Netto)[^\d]{0,10}([\d.,]+)",
        "Total Debts": r"(Total Debts|Debiti Totali)[^\d]{0,10}([\d.,]+)",
    }

    for key, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            try:
                data[key] = float(matches[0][1].replace(".", "").replace(",", "."))
            except:
                data[key] = None
    return data

# Calcolo KPI avanzati
def calculate_kpis(data):
    kpis = {}
    try:
        kpis["ROE"] = round(data["Net Income"] / data["Equity"] * 100, 2)
        kpis["ROA"] = round(data["Net Income"] / data["Total Assets"] * 100, 2)
        kpis["Debt/Equity"] = round(data["Total Debts"] / data["Equity"], 2)
        kpis["EBITDA Margin"] = round(data["EBITDA"] / data["Revenue"] * 100, 2)
    except:
        pass
    return pd.DataFrame([kpis])

# Grafici KPI
def plot_kpis(kpi_df):
    if not kpi_df.empty:
        fig = px.bar(kpi_df.melt(), x='variable', y='value', title='KPI Analysis')
        fig.update_layout(xaxis_title="KPI", yaxis_title="Value", showlegend=False)
        st.plotly_chart(fig)

# Raccomandazioni con GPT opzionale
def generate_recommendations(data, api_key=None):
    if api_key:
        client = OpenAI(api_key=api_key)
        prompt = f"""Genera raccomandazioni sintetiche e professionali per migliorare la performance finanziaria basate su questi dati finanziari:
        {json.dumps(data, indent=2)}

        Rispondi in italiano con punti brevi e pratici."""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=200
        )
        
        recommendations = response.choices[0].message.content.strip().split('\n')
        return recommendations
    else:
        return ["API Key OpenAI non inserita. Raccomandazioni avanzate non disponibili."]
