# --- gestionale/anagrafica.py ---

import json
from dataclasses import dataclass, asdict

@dataclass
class AnagraficaVoce:
    codice: str
    ragione_sociale: str
    tipo: str  # "Cliente" o "Fornitore"
    indirizzo: str
    partita_iva: str
    email: str

    def to_dict(self):
        return asdict(self)

class RegistroAnagrafica:
    def __init__(self):
        self.voci = []

    def aggiungi_voce(self, voce: AnagraficaVoce):
        self.voci.append(voce)

    def cerca_voce(self, codice: str):
        for v in self.voci:
            if v.codice == codice:
                return v
        return None

    def rimuovi_voce(self, codice: str):
        self.voci = [v for v in self.voci if v.codice != codice]

    def to_list(self):
        return [v.to_dict() for v in self.voci]

    def salva_su_file(self, filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_list(), f, indent=2)

    def carica_da_file(self, filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lista = json.load(f)
                for voce in lista:
                    self.aggiungi_voce(AnagraficaVoce(**voce))
        except FileNotFoundError:
            pass
