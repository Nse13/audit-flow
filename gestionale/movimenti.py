def to_dict(self):
    return asdict(self)
def aggiungi_movimento(self, movimento: MovimentoContabile):
    if isinstance(movimento, MovimentoContabile):
        self.movimenti.append(movimento)

def filtra_per_categoria(self, categoria: str):
    return [m for m in self.movimenti if m.categoria == categoria]

def totali_per_categoria(self):
    totali = {}
    for m in self.movimenti:
        totali[m.categoria] = totali.get(m.categoria, 0) + m.importo
    return totali

def verifica_movimenti_sospetti(self, soglia=1_000_000):
    return [m for m in self.movimenti if abs(m.importo) >= soglia]

def verifica_incoerenze_con_registro(self, registro_esterno: list[dict]):
    """Confronta i movimenti con quelli presenti in un registro esterno (es. fornitori, clienti, banche)."""
    differenze = []
    registro_esterno_serializzato = {json.dumps(m, sort_keys=True) for m in registro_esterno}
    for movimento in self.movimenti:
        if json.dumps(movimento.to_dict(), sort_keys=True) not in registro_esterno_serializzato:
            differenze.append(movimento)
    return differenze

def esporta_csv(self, filename="movimenti_export.csv"):
    if not self.movimenti:
        return
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=self.movimenti[0].to_dict().keys())
        writer.writeheader()
        for m in self.movimenti:
            writer.writerow(m.to_dict())

def carica_da_lista(self, lista_dizionari):
    for item in lista_dizionari:
        self.movimenti.append(MovimentoContabile(**item))
