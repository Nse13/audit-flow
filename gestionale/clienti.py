class Cliente:
    def __init__(self, nome, codice_fiscale, saldo_atteso=0.0):
        self.nome = nome
        self.codice_fiscale = codice_fiscale
        self.saldo_atteso = saldo_atteso
        self.movimenti = []

    def registra_movimento(self, movimento):
        self.movimenti.append(movimento)

    def calcola_saldo(self):
        return sum(m.importo for m in self.movimenti)

    def verifica_discrepanze(self):
        saldo_effettivo = self.calcola_saldo()
        return abs(saldo_effettivo - self.saldo_atteso) > 1e-2

class RegistroClienti:
    def __init__(self):
        self.clienti = {}

    def aggiungi_cliente(self, cliente):
        self.clienti[cliente.codice_fiscale] = cliente

    def trova_cliente(self, codice_fiscale):
        return self.clienti.get(codice_fiscale)

    def verifica_tutti(self):
        risultati = []
        for cf, cliente in self.clienti.items():
            if cliente.verifica_discrepanze():
                risultati.append((cliente.nome, cliente.saldo_atteso, cliente.calcola_saldo()))
        return risultati
