from datetime import datetime
import json
from typing import List

class MovimentoContabile:
    def __init__(self, codice: str, descrizione: str, categoria: str, data: str, importo: float, valuta: str = "EUR", standard: str = "OIC"):
        self.codice = codice
        self.descrizione = descrizione
        self.categoria = categoria
        self.data = datetime.strptime(data, "%Y-%m-%d")
        self.importo = importo
        self.valuta = valuta
        self.standard = standard

    def to_dict(self):
        return {
            "codice": self.codice,
            "descrizione": self.descrizione,
            "categoria": self.categoria,
            "data": self.data.strftime("%Y-%m-%d"),
            "importo": self.importo,
            "valuta": self.valuta,
            "standard": self.standard
        }

class RegistroMovimenti:
    def __init__(self):
        self.movimenti: List[MovimentoContabile] = []

    def aggiungi_movimento(self, movimento: MovimentoContabile):
        self.movimenti.append(movimento)

    def rimuovi_movimento(self, codice: str):
        self.movimenti = [m for m in self.movimenti if m.codice != codice]

    def filtra_per_categoria(self, categoria: str) -> List[MovimentoContabile]:
        return [m for m in self.movimenti if m.categoria == categoria]

    def export_json(self, filename: str):
        with open(filename, 'w') as f:
            json.dump([m.to_dict() for m in self.movimenti], f, indent=2)

    def carica_da_json(self, filename: str):
        with open(filename, 'r') as f:
            dati = json.load(f)
            for item in dati:
                movimento = MovimentoContabile(**item)
                self.aggiungi_movimento(movimento)
