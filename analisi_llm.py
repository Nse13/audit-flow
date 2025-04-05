
import requests
import json

# ✅ Funzione: invia a AuditLLM i dati estratti e riceve commento intelligente
def genera_commento_llm(dati_estratti, kpi_df):
    try:
        # Prepara prompt leggibile per AuditLLM
        testo = "Dati estratti dal bilancio:\n"
        for k, v in dati_estratti.items():
            testo += f"- {k}: {v}\n"

        testo += "\nKPI calcolati:\n"
        for _, row in kpi_df.iterrows():
            testo += f"- {row['KPI']}: {row['Valore']}\n"

        prompt = (
            "Sei un revisore esperto. Analizza i dati seguenti e fornisci un commento dettagliato su: "
            "redditività, solidità patrimoniale, performance operativa e eventuali aree di attenzione.\n\n" + testo
        )

        # Invio al modello AuditLLM locale
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": "mistral",
            "prompt": prompt,
            "stream": False
        })

        return response.json()["response"].strip()
    except Exception as e:
        return f"⚠️ Errore AuditLLM: {str(e)}"
