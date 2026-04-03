from flask import Blueprint, render_template, request, session, redirect, url_for

from database.db_operations import save_prediction

from services.health_utils import login_required
from services.predictor import predict_by_disease

prediction_bp = Blueprint("prediction", __name__)


# ======================================================
# DISEASE SELECTION
# ======================================================
@prediction_bp.route("/select_disease", methods=["POST"])
def select_disease():
    if not login_required():
        return redirect(url_for("auth.login"))
    return render_template("input_form.html", disease=request.form.get("disease"))


# ======================================================
# PREDICTION
# ======================================================
@prediction_bp.route("/predict", methods=["POST"])
def predict():
    if not login_required():
        return redirect(url_for("auth.login"))

    user_email = session["user_email"]
    disease = request.form.get("disease")

    result = predict_by_disease(disease, request.form)

    shap_explanation = result["shap_explanation"]
    health_suggestions = result["health_suggestions"]

    session["shap_explanation"] = shap_explanation
    session["health_suggestions"] = health_suggestions

    save_prediction(
        user_id=user_email,
        disease_type=result["disease"],
        input_data=result["input_data"],
        probability=result["probability"],
        risk_level=result["risk"],
        model_accuracy=90.0,
        shap_explanation=shap_explanation,
        health_suggestions=health_suggestions
    )

    return render_template(
        "result.html",
        disease=result["disease"],
        risk=result["risk"],
        probability=round(result["probability"] * 100, 2),
        user=user_email,
        shap_data=result["shap_data"],
        shap_explanation=shap_explanation,
        health_suggestions=health_suggestions
    )