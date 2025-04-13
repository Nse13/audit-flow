# --- piano_conti.py ---

from dataclasses import dataclass
import json
import os

@dataclass
class VoceConto:
    codice: str
    descrizione: str
    tipo: str  # Es. "Attivo", "Passivo", "Costi", "Ricavi"
    categoria: str  # Es. "Immobilizzazioni", "Disponibilità", "Debiti", ecc.

    def to_dict(self):
        return {
            "codice": self.codice,
            "descrizione": self.descrizione,
            "tipo": self.tipo,
            "categoria": self.categoria
        }

class PianoDeiConti:
    def __init__(self):
        self.voci = []

    def aggiungi_voce(self, voce: VoceConto):
        if isinstance(voce, VoceConto):
            self.voci.append(voce)

    def rimuovi_voce(self, codice: str):
        self.voci = [v for v in self.voci if v.codice != codice]

    def cerca_voce(self, codice: str):
        for voce in self.voci:
            if voce.codice == codice:
                return voce
        return None

    def elenco_per_tipo(self, tipo: str):
        return [v for v in self.voci if v.tipo.lower() == tipo.lower()]

    def to_list(self):
        return [v.to_dict() for v in self.voci]

    def salva_su_file(self, filename="piano_conti.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.to_list(), f, indent=2)

    def carica_da_file(self, filename="piano_conti.json"):
        if not os.path.exists(filename):
            return
        with open(filename, encoding="utf-8") as f:
            dati = json.load(f)
            self.voci = [VoceConto(**d) for d in dati]
