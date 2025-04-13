# --- gestionale/fatture.py ---
import json
from dataclasses import dataclass, asdict

@dataclass
class Documento:
    numero: str
    tipo: str  # "Fattura" o "DDT"
    data: str
    cliente: str
    importo: float
    descrizione: str = ""

    def to_dict(self):
        return asdict(self)

class RegistroDocumenti:
    def __init__(self):
        self.documenti = []

    def aggiungi_documento(self, doc: Documento):
        self.documenti.append(doc)

    def to_list(self):
        return [d.to_dict() for d in self.documenti]

    def salva_su_file(self, filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.to_list(), f, indent=2)

    def carica_da_file(self, filename):
        with open(filename, "r", encoding="utf-8") as f:
            lista = json.load(f)
            for item in lista:
                self.documenti.append(Documento(**item))

    def filtra_per_tipo(self, tipo):
        return [d for d in self.documenti if d.tipo == tipo]
