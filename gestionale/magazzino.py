# --- gestionale/magazzino.py ---
import json
from dataclasses import dataclass, asdict

@dataclass
class VoceMagazzino:
    codice_articolo: str
    descrizione: str
    quantita: int
    prezzo_unitario: float
    categoria: str = "Generico"

    def to_dict(self):
        return asdict(self)

class RegistroMagazzino:
    def __init__(self):
        self.voci = []

    def aggiungi_voce(self, voce: VoceMagazzino):
        self.voci.append(voce)

    def to_list(self):
        return [v.to_dict() for v in self.voci]

    def filtra_per_categoria(self, categoria):
        return [v for v in self.voci if v.categoria == categoria]

    def aggiorna_giacenza(self, codice_articolo, variazione_qta):
        for v in self.voci:
            if v.codice_articolo == codice_articolo:
                v.quantita += variazione_qta
                return True
        return False

    def salva_su_file(self, filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.to_list(), f, indent=2)

    def carica_da_file(self, filename):
        with open(filename, "r", encoding="utf-8") as f:
            lista = json.load(f)
            for item in lista:
                self.voci.append(VoceMagazzino(**item))
