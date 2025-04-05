
import requests

# ✅ Funzione che invia un prompt a AuditLLM (modello Mistral via Ollama)
def chiedi_auditllm(prompt):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False
            }
        )
        risposta = response.json()["response"]
        return risposta.strip()
    except Exception as e:
        return f"⚠️ Errore nella richiesta a AuditLLM: {str(e)}"
