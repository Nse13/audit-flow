
import json

def extract_financial_data(text):
    try:
        data = json.loads(text)
        return data
    except json.JSONDecodeError:
        return {"ERROR": {"message": "⚠️ I dati non sono in formato JSON valido. Prova a usare un file diverso o a controllare l'output dell'estrazione."}}
