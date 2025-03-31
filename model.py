# Placeholder per classificatore ML - può essere sostituito con uno reale
def predict_relevance(context, value):
    context = context.lower()
    # Heuristic filter: se compare in sezione ufficiale e valore > soglia
    if "statement" in context or "consolidated" in context or "balance sheet" in context:
        return True
    if value > 1_000_000:
        return True
    return False