from datetime import datetime
from typing import Optional, List
import json

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
                self.aggiungi_movimento(MovimentoContabile(**item))

if __name__ == "__main__":
    registro = RegistroMovimenti()
    movimento1 = MovimentoContabile(
        codice="OIC_01",
        descrizione="Fattura attiva",
        categoria="Vendite",
        data="2025-04-02",
        importo=1000.0
    )
    registro.aggiungi_movimento(movimento1)
    registro.export_json("movimenti_export.json")
