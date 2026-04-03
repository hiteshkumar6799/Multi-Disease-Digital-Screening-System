import random
import string
import re
from flask import session


def login_required():
    """
    Returns True if a user is logged in.
    Original helper from app.py.
    """
    return "user_email" in session


def generate_otp():
    """
    6-digit numeric OTP generator.
    """
    return ''.join(random.choices(string.digits, k=6))


def is_strong_password(password):
    """
    Enforces strong password policy:
    - Min 8 chars
    - Uppercase
    - Lowercase
    - Digit
    - Special character
    """
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[^A-Za-z0-9]", password):
        return False
    return True


def generate_health_suggestions(disease, risk, shap_data):
    """
    Your existing health suggestions logic.
    """
    if risk == "Low Risk":
        return {
            "level": "low",
            "title": "You are currently at low health risk",
            "message": "Maintain a healthy lifestyle to stay protected.",
            "items": [
                "Follow a balanced and nutritious diet",
                "Engage in regular physical activity",
                "Stay hydrated throughout the day",
                "Go for routine health checkups"
            ]
        }

    DIABETES_MAP = {
        "bmi": "Reduce calorie intake and increase fiber-rich foods.",
        "glucose": "Avoid sugary foods and refined carbohydrates.",
        "bp": "Limit salt intake and manage stress.",
        "age": "Maintain regular meal timing and monitoring."
    }

    HEART_MAP = {
        "chol": "Reduce saturated fats and fried foods.",
        "bp": "Follow a low-sodium diet.",
        "age": "Engage in light daily physical activity.",
        "thalach": "Maintain cardiovascular fitness through walking."
    }

    KIDNEY_MAP = {
        "renal_function": "Limit protein intake as advised.",
        "electrolyte_balance": "Avoid foods high in sodium and potassium.",
        "blood_pressure": "Control salt intake strictly.",
        "urine_sugar": "Monitor blood sugar regularly."
    }

    disease_map = (
        DIABETES_MAP if disease == "diabetes"
        else HEART_MAP if disease == "heart"
        else KIDNEY_MAP
    )

    suggestions = []
    for feature in shap_data.keys():
        if feature in disease_map:
            suggestions.append(disease_map[feature])

    if not suggestions:
        suggestions.append("Maintain a balanced diet and healthy lifestyle.")

    if risk == "High Risk":
        return {
            "level": "high",
            "title": "High Risk Detected",
            "message": "Please consult a medical professional immediately.",
            "items": suggestions
        }

    return {
        "level": "medium",
        "title": "Moderate Risk Detected",
        "message": "Lifestyle and dietary changes can help reduce future risk.",
        "items": suggestions
    }