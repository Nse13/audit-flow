# === gestionale/inventario.py ===

class ProdottoMagazzino:
    def __init__(self, codice, descrizione, quantita, prezzo_unitario, categoria="Generico"):
        self.codice = codice
        self.descrizione = descrizione
        self.quantita = quantita
        self.prezzo_unitario = prezzo_unitario
        self.categoria = categoria

    def valore_totale(self):
        return self.quantita * self.prezzo_unitario

class Magazzino:
    def __init__(self):
        self.prodotti = {}

    def aggiungi_prodotto(self, prodotto):
        self.prodotti[prodotto.codice] = prodotto

    def aggiorna_quantita(self, codice, variazione):
        if codice in self.prodotti:
            self.prodotti[codice].quantita += variazione

    def rimuovi_prodotto(self, codice):
        if codice in self.prodotti:
            del self.prodotti[codice]

    def inventario_totale(self):
        return sum(p.valore_totale() for p in self.prodotti.values())

    def elenco_prodotti(self):
        return [vars(p) for p in self.prodotti.values()]
