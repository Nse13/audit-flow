import fitz  # PyMuPDF
import pandas as pd
import openai
import os
import pytesseract
from PIL import Image
import io

def extract_financial_data(file_path, use_gpt=False):
    """
    Estrae i dati finanziari da un file PDF utilizzando OCR.
    Se use_gpt è True, utilizza GPT per analizzare il testo estratto.
    """
    text = ""

    # Estrazione del testo dal PDF
    with fitz.open(file_path) as doc:
        for page in doc:
            # Prova a ottenere il testo direttamente
            page_text = page.get_text()
            if page_text.strip():
                text += page_text
            else:
                # Se non c'è testo, prova con OCR
                pix = page.get_pixmap()
                img = Image.open(io.BytesIO(pix.tobytes()))
                page_text = pytesseract.image_to_string(img, lang='ita')
                text += page_text

    if use_gpt:
        # Analisi del testo con GPT
        openai.api_key = os.getenv("OPENAI_API_KEY")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Sei un assistente esperto in finanza."},
                {"role": "user", "content": f"Analizza il seguente testo e estrai i principali dati finanziari:\n{text}"}
            ]
        )
        analysis = response.choices[0].message['content'].strip()
        return analysis
    else:
        # Analisi manuale del testo per estrarre i dati finanziari
        data = parse_financial_data(text)
        return data

def parse_financial_data(text):
    """
    Analizza manualmente il testo per estrarre i dati finanziari.
    """
    data = {}
    # Implementa qui la logica per analizzare il testo e estrarre i dati finanziari
    # Ad esempio, puoi cercare pattern specifici nel testo per trovare i valori desiderati
    return data
