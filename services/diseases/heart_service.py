import joblib
import numpy as np
import shap

from services.db_utils import get_float
from services.shap_utils import compute_shap_percentages

heart_model = joblib.load("models/heart_xgboost_final.pkl")
heart_explainer = shap.TreeExplainer(heart_model)


def predict_heart(form):
    fields = ["age", "sex", "cp", "bp", "chol", "ecg", "thalach", "exang"]
    X = np.array([[get_float(form, f) for f in fields]])

    prob = float(heart_model.predict_proba(X)[0][1])
    input_data = dict(zip(fields, X[0]))

    shap_data = compute_shap_percentages(heart_explainer, X, fields)

    return {
        "disease": "heart",
        "probability": prob,
        "input_data": input_data,
        "shap_data": shap_data
    }