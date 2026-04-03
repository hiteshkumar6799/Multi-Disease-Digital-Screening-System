from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
    Response,
    session,
)
from io import StringIO
from services import admin_service as admin_svc
from services.db_utils import get_db_connection
from services.health_utils import login_required
import csv


admin = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required():
    if not login_required():
        return False

    user_email = session.get("user_email")
    if not user_email:
        return False

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_admin FROM users WHERE email = %s", (user_email,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return False

    return bool(row[0])


@admin.before_request
def restrict_to_admins():
    if not login_required():
        return redirect(url_for("auth.login"))

    if not admin_required():
        abort(403)


@admin.route("/dashboard")
def dashboard():
    stats = admin_svc.get_dashboard_stats()

    return render_template(
        "admin/admin_dashboard.html",
        total_users=stats["total_users"],
        total_predictions=stats["total_predictions"],
        high_risk_count=stats["high_risk_count"],
        high_risk_pct=stats["high_risk_pct"],
        latest_predictions=stats["latest_predictions"],
        predictions_today=stats["predictions_today"],
        most_predicted_disease=stats["most_predicted_disease"],
        disease_labels=stats["disease_labels"],
        disease_counts=stats["disease_counts"],
        risk_labels=stats["risk_labels"],
        risk_counts=stats["risk_counts"],
        trend_labels=stats["trend_labels"],
        trend_counts=stats["trend_counts"],
        top_users=stats["top_users"],
        latest_high_risk=stats["latest_high_risk"],
    )


@admin.route("/users")
def users():
    users = admin_svc.get_users()
    return render_template("admin/users.html", users=users)


@admin.post("/users/<int:user_id>/toggle_active")
def toggle_user_active(user_id):
    ok = admin_svc.toggle_user(user_id)
    flash(
        "User status updated." if ok else "User not found.",
        "success" if ok else "error",
    )
    return redirect(url_for("admin.users"))


@admin.post("/users/<int:user_id>/delete")
def delete_user(user_id):
    admin_svc.delete_user(user_id)
    flash("User deleted.", "success")
    return redirect(url_for("admin.users"))


@admin.route("/predictions")
def predictions():
    disease = request.args.get("disease") or None
    risk = request.args.get("risk") or None
    date_from = request.args.get("from") or None
    date_to = request.args.get("to") or None

    rows = admin_svc.get_predictions_with_filters(disease, risk, date_from, date_to)
    diseases = admin_svc.get_disease_types()
    risks = ["Low Risk", "Medium Risk", "High Risk"]

    return render_template(
        "admin/predictions.html",
        predictions=rows,
        diseases=diseases,
        risks=risks,
        current_disease=disease,
        current_risk=risk,
        current_from=date_from,
        current_to=date_to,
    )


@admin.route("/analytics")
def analytics():
    stats = admin_svc.get_dashboard_stats()
    analytics_data = admin_svc.get_analytics_data()

    return render_template(
        "admin/analytics.html",
        total_users=stats["total_users"],
        total_predictions=stats["total_predictions"],
        high_risk_count=stats["high_risk_count"],
        high_risk_pct=stats["high_risk_pct"],
        predictions_today=analytics_data["predictions_today"],
        new_users_today=analytics_data["new_users_today"],
        most_predicted_disease=analytics_data["most_predicted_disease"],
        disease_labels=analytics_data["disease_labels"],
        disease_counts=analytics_data["disease_counts"],
        risk_labels=analytics_data["risk_labels"],
        risk_counts=analytics_data["risk_counts"],
        trend_labels=analytics_data["trend_labels"],
        trend_counts=analytics_data["trend_counts"],
        high_risk_trend_labels=analytics_data["high_risk_trend_labels"],
        high_risk_trend_counts=analytics_data["high_risk_trend_counts"],
        avg_prob_labels=analytics_data["avg_prob_labels"],
        avg_prob_values=analytics_data["avg_prob_values"],
        high_risk_disease_labels=analytics_data["high_risk_disease_labels"],
        high_risk_disease_counts=analytics_data["high_risk_disease_counts"],
        top_users=analytics_data["top_users"],
        latest_high_risk=analytics_data["latest_high_risk"],
    )


@admin.route("/export_csv")
def export_csv():
    rows = admin_svc.get_all_predictions_for_csv()

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(
        ["id", "user_email", "disease_type", "risk_level", "probability", "timestamp"]
    )

    for r in rows:
        cw.writerow(r)

    output = Response(si.getvalue(), mimetype="text/csv")
    output.headers["Content-Disposition"] = "attachment; filename=predictions.csv"
    return output