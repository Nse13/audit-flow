class Fornitore:
    def __init__(self, nome, partita_iva, saldo_atteso=0.0):
        self.nome = nome
        self.partita_iva = partita_iva
        self.saldo_atteso = saldo_atteso
        self.movimenti = []

    def registra_movimento(self, movimento):
        self.movimenti.append(movimento)

    def calcola_saldo(self):
        return sum(m.importo for m in self.movimenti)

    def verifica_discrepanze(self):
        saldo_effettivo = self.calcola_saldo()
        return abs(saldo_effettivo - self.saldo_atteso) > 1e-2

class RegistroFornitori:
    def __init__(self):
        self.fornitori = {}

    def aggiungi_fornitore(self, fornitore):
        self.fornitori[fornitore.partita_iva] = fornitore

    def trova_fornitore(self, partita_iva):
        return self.fornitori.get(partita_iva)

    def verifica_tutti(self):
        risultati = []
        for piva, fornitore in self.fornitori.items():
            if fornitore.verifica_discrepanze():
                risultati.append((fornitore.nome, fornitore.saldo_atteso, fornitore.calcola_saldo()))
        return risultati
