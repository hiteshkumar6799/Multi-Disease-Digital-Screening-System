import joblib
import numpy as np
import shap

from services.db_utils import get_float
from services.shap_utils import compute_shap_percentages

kidney_model = joblib.load("models/kidney_xgboost_final.pkl")
kidney_scaler = joblib.load("models/kidney_scaler.pkl")
kidney_explainer = shap.TreeExplainer(kidney_model)


def predict_kidney(form):
    urea, creat, sod, pot, hemo, pcv, sugar, bp, age = [
        get_float(form, f)
        for f in ["urea", "creatinine", "sodium", "potassium", "hemo", "pcv", "sugar", "bp", "age"]
    ]

    engineered = np.array([[
        urea + creat,
        sod + pot,
        hemo + pcv,
        sugar,
        bp,
        int(hemo < 12),
        int(pot > 5),
        age
    ]])

    engineered_scaled = kidney_scaler.transform(engineered)
    prob = float(kidney_model.predict_proba(engineered_scaled)[0][1])

    input_data = {
        "urea": urea,
        "creatinine": creat,
        "sodium": sod,
        "potassium": pot,
        "hemo": hemo,
        "pcv": pcv,
        "sugar": sugar,
        "bp": bp,
        "age": age
    }

    kidney_features = [
        "renal_function",
        "electrolyte_balance",
        "blood_health",
        "urine_sugar",
        "blood_pressure",
        "anemia_flag",
        "electrolyte_risk",
        "age"
    ]

    shap_data = compute_shap_percentages(
        kidney_explainer, engineered_scaled, kidney_features
    )

    return {
        "disease": "kidney",
        "probability": prob,
        "input_data": input_data,
        "shap_data": shap_data
    }