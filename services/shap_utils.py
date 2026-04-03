import numpy as np


def compute_shap_percentages(explainer, X, feature_names):
    """
    SAFE SHAP handler for binary XGBoost models.
    Returns percentage contribution per feature.
    Original implementation from app.py.
    """
    shap_values = explainer.shap_values(X)

    if isinstance(shap_values, list):
        shap_vals = shap_values[1] if len(shap_values) > 1 else shap_values[0]
    else:
        shap_vals = shap_values

    shap_vals = shap_vals[0]

    abs_vals = np.abs(shap_vals)
    total = abs_vals.sum() if abs_vals.sum() != 0 else 1.0

    return {
        feature_names[i]: float(round((abs_vals[i] / total) * 100, 2))
        for i in range(len(feature_names))
    }


def top_5_shap(shap_data: dict):
    """
    Keep top 5 contributors and combine rest as 'Others'.
    """
    sorted_items = sorted(shap_data.items(), key=lambda x: x[1], reverse=True)
    top_5 = sorted_items[:5]
    others = sorted_items[5:]

    final_shap = dict(top_5)

    if others:
        final_shap["Others"] = round(sum(v for _, v in others), 2)

    return final_shap


def generate_shap_explanation(disease, shap_data):
    """
    Disease-specific human readable SHAP explanation.
    """
    items = sorted(shap_data.items(), key=lambda x: x[1], reverse=True)

    if not items:
        return "No significant contributing factors identified."

    if len(items) == 1:
        f, v = items[0]
        return f"{f.replace('_',' ').title()} ({v}%) is the main contributing factor."

    f1, v1 = items[0]
    f2, v2 = items[1]

    f1 = f1.replace("_", " ").title()
    f2 = f2.replace("_", " ").title()

    v1 = round(v1, 1)
    v2 = round(v2, 1)

    if disease == "diabetes":
        return (
            f"High {f1.lower()} ({v1}%) and {f2.lower()} ({v2}%) "
            "are the primary contributors to diabetes risk."
        )

    v1 = round(v1, 1)
    v2 = round(v2, 1)

    if disease == "heart":
        return (
            f"{f1} ({v1}%) and {f2.lower()} ({v2}%) "
            "are the major factors contributing to heart disease risk."
        )

    v1 = round(v1, 1)
    v2 = round(v2, 1)

    if disease == "kidney":
        return (
            f"{f1} ({v1}%) and {f2.lower()} ({v2}%) "
            "strongly influence kidney disease risk."
        )

    return (
        f"{f1} ({v1}%) and {f2} ({v2}%) "
        "are the key contributors to the prediction."
    )