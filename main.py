from gestionale import MovimentoContabile, RegistroMovimenti

def main():
    registro = RegistroMovimenti()

    movimento1 = MovimentoContabile(
        codice="IAS_02",
        descrizione="Svalutazione magazzino",
        categoria="Magazzino",
        data="2025-04-02",
        importo=1200.50,
        standard="IAS"
    )

    registro.aggiungi_movimento(movimento1)
    registro.export_json("output_movimenti.json")
    print("Movimento salvato correttamente.")

if __name__ == "__main__":
    main()
