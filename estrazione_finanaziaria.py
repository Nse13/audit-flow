import pdfplumber
import re
import json

# === CONFIGURAZIONE ===
pdf_path = "Stellantis_NV_2024.pdf"  # rinomina il file PDF al momento del caricamento
output_json = "dati_auditflow_2024.json"

# === VOCI TARGET DA ESTRARRE ===
target_keywords = [
    "Total Assets",
    "Cash and cash equivalents",
    "Total Equity",
    "Trade payables",
    "Inventories",
    "Long-term debt",
    "Short-term debt",
    "Total Liabilities",
    "Property, plant and equipment",
    "Revenues"
]

# === FUNZIONE PER MATCHING FUZZY DELLE VOCI ===
def matches_target(row, keywords):
    row_text = " ".join([cell for cell in row if cell])
    for key in keywords:
        if key.lower() in row_text.lower():
            return key
    return None

# === FUNZIONE PER ESTRARRE IL PRIMO NUMERO PLAUSIBILE (>=1000) ===
def extract_better_value_from_row(row):
    numeric_values = []
    for cell in reversed(row):
        if cell:
            match = re.search(r"[\d.,]+", cell)
            if match:
                raw_number = match.group().replace(",", "").replace(".", "")
                try:
                    value = int(raw_number)
                    if value >= 1000:
                        numeric_values.append(value)
                except ValueError:
                    continue
    return numeric_values[0] if numeric_values else None

# === ESTRAZIONE DAL PDF ===
extracted_candidates = {}
final_data_cleaned = {}

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            for row in table:
                match = matches_target(row, target_keywords)
                if match:
                    if match not in extracted_candidates:
                        extracted_candidates[match] = []
                    extracted_candidates[match].append(row)

# === SELEZIONE DEI VALORI CORRETTI ===
for key, rows in extracted_candidates.items():
    for row in rows:
        val = extract_better_value_from_row(row)
        if val:
            final_data_cleaned[key] = val
            break

# === SALVATAGGIO SU JSON ===
with open(output_json, "w") as f:
    json.dump(final_data_cleaned, f, indent=2)

print("Estrazione completata. Dati salvati in:", output_json)
