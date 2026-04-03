import joblib
import numpy as np
import shap

from services.db_utils import get_float
from services.shap_utils import compute_shap_percentages

diabetes_model = joblib.load("models/diabetes_xgboost_final.pkl")
diabetes_scaler = joblib.load("models/diabetes_scaler.pkl")
diabetes_explainer = shap.TreeExplainer(diabetes_model)


def predict_diabetes(form):
    fields = ["pregnancies", "glucose", "bp", "skin", "insulin", "bmi", "dpf", "age"]
    X = np.array([[get_float(form, f) for f in fields]])
    X_scaled = diabetes_scaler.transform(X)

    prob = float(diabetes_model.predict_proba(X_scaled)[0][1])
    input_data = dict(zip(fields, X[0]))

    shap_data = compute_shap_percentages(diabetes_explainer, X_scaled, fields)

    return {
        "disease": "diabetes",
        "probability": prob,
        "input_data": input_data,
        "shap_data": shap_data
    }