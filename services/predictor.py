from services.shap_utils import top_5_shap, generate_shap_explanation
from services.health_utils import generate_health_suggestions

from services.diseases.diabetes_service import predict_diabetes
from services.diseases.heart_service import predict_heart
from services.diseases.kidney_service import predict_kidney


def get_risk_level(prob):
    if prob < 0.3:
        return "Low Risk"
    elif prob < 0.7:
        return "Medium Risk"
    return "High Risk"


DISEASE_SERVICES = {
    "diabetes": predict_diabetes,
    "heart": predict_heart,
    "kidney": predict_kidney,
}


def predict_by_disease(disease, form):
    if disease not in DISEASE_SERVICES:
        raise ValueError("Unsupported disease selected.")

    result = DISEASE_SERVICES[disease](form)

    prob = result["probability"]
    shap_data = top_5_shap(result["shap_data"])
    risk = get_risk_level(prob)
    shap_explanation = generate_shap_explanation(disease, shap_data)
    health_suggestions = generate_health_suggestions(disease, risk, shap_data)

    return {
        "disease": disease,
        "probability": prob,
        "risk": risk,
        "input_data": result["input_data"],
        "shap_data": shap_data,
        "shap_explanation": shap_explanation,
        "health_suggestions": health_suggestions
    }