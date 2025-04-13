import datetime

class MovimentoContabile:
    def __init__(self, codice, descrizione, categoria, data, importo, valuta, standard):
        self.codice = codice
        self.descrizione = descrizione
        self.categoria = categoria
        self.data = data  # stringa "YYYY-MM-DD"
        self.importo = importo
        self.valuta = valuta
        self.standard = standard

    def to_dict(self):
        return {
            "Codice": self.codice,
            "Descrizione": self.descrizione,
            "Categoria": self.categoria,
            "Data": self.data,
            "Importo": self.importo,
            "Valuta": self.valuta,
            "Standard": self.standard
        }

class RegistroMovimenti:
    def __init__(self):
        self.movimenti = []

    def aggiungi_movimento(self, movimento):
        if isinstance(movimento, MovimentoContabile):
            self.movimenti.append(movimento)

    def filtra_per_categoria(self, categoria):
        return [m for m in self.movimenti if m.categoria == categoria]

    def totali_per_categoria(self):
        totali = {}
        for m in self.movimenti:
            totali[m.categoria] = totali.get(m.categoria, 0) + m.importo
        return totali

    def verifica_movimenti_sospetti(self, soglia=1_000_000):
        return [m for m in self.movimenti if abs(m.importo) >= soglia]
