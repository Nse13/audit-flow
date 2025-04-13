# === gestionale/banche.py ===

class ContoBancario:
    def __init__(self, iban, banca, saldo_atteso=0.0):
        self.iban = iban
        self.banca = banca
        self.saldo_atteso = saldo_atteso
        self.movimenti = []

    def registra_movimento(self, movimento):
        self.movimenti.append(movimento)

    def calcola_saldo(self):
        return sum(m.importo for m in self.movimenti)

    def verifica_riconciliazione(self):
        saldo_calcolato = self.calcola_saldo()
        return abs(saldo_calcolato - self.saldo_atteso) > 1e-2

class RegistroContiBancari:
    def __init__(self):
        self.conti = {}

    def aggiungi_conto(self, conto):
        self.conti[conto.iban] = conto

    def trova_conto(self, iban):
        return self.conti.get(iban)

    def riconcilia_tutti(self):
        risultati = []
        for iban, conto in self.conti.items():
            if conto.verifica_riconciliazione():
                risultati.append((conto.iban, conto.saldo_atteso, conto.calcola_saldo()))
        return risultati
