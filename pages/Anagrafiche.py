# --- gestionale/anagrafiche.py ---
import os
import json

ANAGRAFICHE_FILE = "gestionale/anagrafiche_clienti_fornitori.json"

def carica_anagrafiche():
    if not os.path.exists(ANAGRAFICHE_FILE):
        return []
    with open(ANAGRAFICHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def salva_anagrafiche(anagrafiche):
    with open(ANAGRAFICHE_FILE, "w", encoding="utf-8") as f:
        json.dump(anagrafiche, f, indent=2, ensure_ascii=False)

def aggiungi_anagrafica(anagrafica):
    anagrafiche = carica_anagrafiche()
    anagrafiche.append(anagrafica)
    salva_anagrafiche(anagrafiche)

def elimina_anagrafica(index):
    anagrafiche = carica_anagrafiche()
    if 0 <= index < len(anagrafiche):
        del anagrafiche[index]
        salva_anagrafiche(anagrafiche)
