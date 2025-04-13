# --- gestionale/piano_conti.py ---

class VoceConto:
    def __init__(self, codice, descrizione, tipo):
        self.codice = codice
        self.descrizione = descrizione
        self.tipo = tipo  # es: "Attivo", "Passivo", "Costo", "Ricavo"

    def to_dict(self):
        return {
            "Codice": self.codice,
            "Descrizione": self.descrizione,
            "Tipo": self.tipo
        }

class PianoDeiConti:
    def __init__(self):
        self.voci = []

    def aggiungi_voce(self, voce):
        if isinstance(voce, VoceConto):
            self.voci.append(voce)

    def rimuovi_voce(self, codice):
        self.voci = [v for v in self.voci if v.codice != codice]

    def trova_per_tipo(self, tipo):
        return [v for v in self.voci if v.tipo == tipo]

    def carica_da_file(self, filename):
        import json
        import os
        if os.path.exists(filename):
            with open(filename, encoding="utf-8") as f:
                dati = json.load(f)
                self.voci = [VoceConto(**item) for item in dati]

    def salva_su_file(self, filename):
        import json
        with open(filename, "w", encoding="utf-8") as f:
            json.dump([v.to_dict() for v in self.voci], f, indent=2)

    def to_list(self):
        return [v.to_dict() for v in self.voci]
