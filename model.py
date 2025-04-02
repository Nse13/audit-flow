# Funzioni di machine learning per analisi avanzate (già definite precedentemente)
# model.py
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

# Modello per determinare la rilevanza dei dati estratti
def build_relevance_model(X_train, y_train):
    pipeline = make_pipeline(StandardScaler(), RandomForestClassifier(n_estimators=100, random_state=42))
    pipeline.fit(X_train, y_train)
    return pipeline

# Funzione per predire la rilevanza di nuovi dati
def predict_relevance(model, X_test):
    return model.predict(X_test), model.predict_proba(X_test)

# Funzione per aggiornare il modello con nuovi dati (opzionale per auto-apprendimento continuo)
def update_model(model, X_new, y_new):
    model.fit(X_new, y_new)
    return model
