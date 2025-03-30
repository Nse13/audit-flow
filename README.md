
# 📊 Audit Flow Pro+

**Audit Flow Pro+** è una web app professionale per l'analisi di bilanci aziendali, progettata per auditor, studenti, analisti e professionisti.

---

## ✅ Funzionalità principali

- 🔍 Estrazione dati da **PDF** (anche con OCR)
- 📈 Analisi diretta da **Excel e CSV** multi-anno
- 🤖 Supporto **GPT (opzionale)** per completamento intelligente dei dati
- 🧠 **Machine Learning** per clustering semantico del testo dei report
- 📉 Calcolo automatico di KPI:
  - ROE, Net Margin, EBITDA Margin, Debt/Equity
- 📊 Grafici interattivi (Plotly)
- 📂 Download del report PDF generato

---

## 🧪 Formati supportati

- `.pdf` (PDF anche scansionati)
- `.xlsx` / `.xls` (Excel)
- `.csv`

---

## 🚀 Come avviare l'app localmente

1. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

2. Avvia l'app con Streamlit:
```bash
streamlit run app_auditflow_final_with_ml.py
```

3. Apri il browser su:
```
http://localhost:8501
```

---

## 🔐 OpenAI (facoltativo)

Se vuoi attivare il completamento GPT, inserisci la tua API Key nella barra laterale.

Puoi ottenerla su: https://platform.openai.com/account/api-keys

---

## 👤 Autore

Realizzato da **Manuel Gobino** con il supporto dell'AI per lo sviluppo intelligente e scalabile.

---

## 📄 Licenza

Distribuito per uso personale, formativo e professionale. Tutti i diritti riservati.
