from database import db_operations as db_ops


def get_dashboard_stats():
    total_users = db_ops.count_users()
    total_predictions = db_ops.count_predictions()
    high_risk_count = db_ops.count_predictions_by_risk("High Risk")
    high_risk_pct = (high_risk_count / total_predictions * 100) if total_predictions else 0
    latest_predictions = db_ops.get_latest_predictions(10)

    predictions_today = db_ops.count_predictions_today()
    most_predicted_disease = db_ops.get_most_predicted_disease()

    disease_distribution = db_ops.get_disease_distribution()
    risk_distribution = db_ops.get_risk_distribution()
    predictions_trend = db_ops.get_predictions_trend()
    top_users = db_ops.get_top_active_users(5)
    latest_high_risk = db_ops.get_latest_high_risk_predictions(5)

    disease_labels = [row[0].title() if row[0] else "Unknown" for row in disease_distribution]
    disease_counts = [row[1] for row in disease_distribution]

    risk_labels = [row[0].title() if row[0] else "Unknown" for row in risk_distribution]
    risk_counts = [row[1] for row in risk_distribution]

    trend_labels = [str(row[0]) for row in predictions_trend]
    trend_counts = [row[1] for row in predictions_trend]

    return {
        "total_users": total_users,
        "total_predictions": total_predictions,
        "high_risk_count": high_risk_count,
        "high_risk_pct": round(high_risk_pct, 1),
        "latest_predictions": latest_predictions,
        "predictions_today": predictions_today,
        "most_predicted_disease": most_predicted_disease.title() if most_predicted_disease else "N/A",
        "disease_labels": disease_labels,
        "disease_counts": disease_counts,
        "risk_labels": risk_labels,
        "risk_counts": risk_counts,
        "trend_labels": trend_labels,
        "trend_counts": trend_counts,
        "top_users": top_users,
        "latest_high_risk": latest_high_risk,
    }


def get_analytics_data():
    predictions_today = db_ops.count_predictions_today()
    new_users_today = db_ops.count_new_users_today()
    most_predicted_disease = db_ops.get_most_predicted_disease()

    disease_distribution = db_ops.get_disease_distribution()
    risk_distribution = db_ops.get_risk_distribution()
    predictions_trend = db_ops.get_predictions_trend()
    high_risk_trend = db_ops.get_high_risk_trend()
    avg_probability_by_disease = db_ops.get_avg_probability_by_disease()
    high_risk_by_disease = db_ops.get_high_risk_by_disease()
    top_users = db_ops.get_top_active_users(10)
    latest_high_risk = db_ops.get_latest_high_risk_predictions(10)

    disease_labels = [row[0].title() if row[0] else "Unknown" for row in disease_distribution]
    disease_counts = [row[1] for row in disease_distribution]

    risk_labels = [row[0].title() if row[0] else "Unknown" for row in risk_distribution]
    risk_counts = [row[1] for row in risk_distribution]

    trend_labels = [str(row[0]) for row in predictions_trend]
    trend_counts = [row[1] for row in predictions_trend]

    high_risk_trend_labels = [str(row[0]) for row in high_risk_trend]
    high_risk_trend_counts = [row[1] for row in high_risk_trend]

    avg_prob_labels = [row[0].title() if row[0] else "Unknown" for row in avg_probability_by_disease]
    avg_prob_values = [float(row[1]) for row in avg_probability_by_disease]

    high_risk_disease_labels = [row[0].title() if row[0] else "Unknown" for row in high_risk_by_disease]
    high_risk_disease_counts = [row[1] for row in high_risk_by_disease]

    return {
        "predictions_today": predictions_today,
        "new_users_today": new_users_today,
        "most_predicted_disease": most_predicted_disease.title() if most_predicted_disease else "N/A",
        "disease_labels": disease_labels,
        "disease_counts": disease_counts,
        "risk_labels": risk_labels,
        "risk_counts": risk_counts,
        "trend_labels": trend_labels,
        "trend_counts": trend_counts,
        "high_risk_trend_labels": high_risk_trend_labels,
        "high_risk_trend_counts": high_risk_trend_counts,
        "avg_prob_labels": avg_prob_labels,
        "avg_prob_values": avg_prob_values,
        "high_risk_disease_labels": high_risk_disease_labels,
        "high_risk_disease_counts": high_risk_disease_counts,
        "top_users": top_users,
        "latest_high_risk": latest_high_risk,
    }


def get_users():
    return db_ops.get_all_users()


def toggle_user(user_id: int) -> bool:
    return db_ops.toggle_user_active(user_id)


def delete_user(user_id: int):
    db_ops.delete_user(user_id)


def get_predictions_with_filters(disease, risk, date_from, date_to):
    return db_ops.get_all_predictions_with_filters(
        disease_type=disease,
        risk_level=risk,
        date_from=date_from,
        date_to=date_to,
    )


def get_disease_types():
    return db_ops.get_all_disease_types()


def get_all_predictions_for_csv():
    return db_ops.get_all_predictions_for_csv()