from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for,
    send_file,
    flash,
)
import io
import ast
import json
import pandas as pd

from datetime import datetime
from textwrap import wrap

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from services.db_utils import get_db_connection, safe_float
from services.health_utils import login_required

reports_bp = Blueprint("reports", __name__)


# ---------------- ACCOUNT HISTORY ----------------
@reports_bp.route("/account_history")
def account_history():
    if not login_required():
        return redirect(url_for("auth.login"))

    search = request.args.get("search", "").strip()
    risk_filter = request.args.get("risk", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    base_query = """
        SELECT id, disease_type, probability, risk_level, timestamp
        FROM user_predictions
        WHERE user_id=%s
    """
    params = [session["user_email"]]

    if search:
        base_query += " AND disease_type ILIKE %s"
        params.append(f"%{search}%")

    if risk_filter:
        base_query += " AND risk_level=%s"
        params.append(risk_filter)

    table_query = base_query + " ORDER BY timestamp DESC"
    cursor.execute(table_query, params)
    predictions_rows = cursor.fetchall()

    chart_query = base_query + " ORDER BY timestamp ASC"
    cursor.execute(chart_query, params)
    chart_rows = cursor.fetchall()

    conn.close()

    updated_predictions = []

    for row in predictions_rows:
        dt = row[4]
        if isinstance(dt, str):
            timestamp_str = dt
        else:
            timestamp_str = dt.strftime("%d %b %Y, %I:%M %p")

        updated_predictions.append({
            "id": row[0],
            "disease_type": row[1],
            "probability": row[2],
            "risk_level": row[3],
            "timestamp": timestamp_str
        })

    disease_latest = {}
    disease_previous = {}

    for row in chart_rows:
        disease = row[1]
        prob = round(row[2] * 100, 2)

        if disease not in disease_latest:
            disease_latest[disease] = prob
            disease_previous[disease] = None
        else:
            disease_previous[disease] = disease_latest[disease]
            disease_latest[disease] = prob

    chart_labels = []
    chart_values = []
    chart_colors = []

    for disease in disease_latest:
        chart_labels.append(disease.capitalize())
        chart_values.append(disease_latest[disease])

        if disease_previous[disease] is None:
            chart_colors.append("#3498db")
        elif disease_latest[disease] < disease_previous[disease]:
            chart_colors.append("#27ae60")
        else:
            chart_colors.append("#c0392b")

    return render_template(
        "account_history.html",
        predictions=updated_predictions,
        total_predictions=len(updated_predictions),
        search=search,
        risk_filter=risk_filter,
        chart_labels=chart_labels,
        chart_values=chart_values,
        chart_colors=chart_colors
    )


# ---------------- DOWNLOAD SPECIFIC PDF ----------------
@reports_bp.route("/download_pdf/<int:prediction_id>")
def download_specific_pdf(prediction_id):
    if not login_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT disease_type, input_data, probability, risk_level,
               shap_explanation, health_suggestions, timestamp
        FROM user_predictions
        WHERE id=%s AND user_id=%s
    """, (prediction_id, session["user_email"]))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return "Report not found"

    disease, input_data, probability, risk, shap_explanation, health_suggestions, timestamp = row

    if isinstance(timestamp, str):
        formatted_time = timestamp
    else:
        formatted_time = timestamp.strftime("%d %b %Y, %I:%M %p")

    input_data = ast.literal_eval(input_data)
    probability = float(probability)

    if health_suggestions:
        health_suggestions = json.loads(health_suggestions)
    else:
        health_suggestions = None

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    y = 800

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(300, y, "AI Healthcare Screening Report")
    y -= 25

    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(300, y, f"Generated on: {formatted_time}")
    y -= 30

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, y, f"User: {session['user_email']}")
    y -= 18

    pdf.drawString(50, y, f"Disease: {disease.capitalize()}")
    y -= 30

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Input Parameters")
    y -= 20

    pdf.setFont("Helvetica", 11)
    for k, v in input_data.items():
        pdf.drawString(60, y, f"{k.replace('_', ' ').title()}: {v}")
        y -= 16

    y -= 20

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, f"Risk Level: {risk}")
    y -= 20

    pdf.drawString(50, y, f"Probability: {round(probability * 100, 2)}%")

    if shap_explanation:
        y -= 30
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, "Why this risk level?")
        y -= 18

        pdf.setFont("Helvetica", 11)
        wrapped_text = wrap(shap_explanation, 80)
        text_object = pdf.beginText(60, y)

        for line in wrapped_text:
            text_object.textLine(line)

        pdf.drawText(text_object)
        y -= 14 * len(wrapped_text)

    if health_suggestions:
        y -= 30
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, "Personalized Health Suggestions")
        y -= 18

        pdf.setFont("Helvetica", 11)

        title_line = f"{health_suggestions['title']} – {health_suggestions['message']}"
        for line in wrap(title_line, 80):
            pdf.drawString(60, y, line)
            y -= 14

        y -= 10

        for suggestion in health_suggestions["items"]:
            wrapped_lines = wrap(f"- {suggestion}", 75)
            for line in wrapped_lines:
                pdf.drawString(70, y, line)
                y -= 14

        if health_suggestions["level"] == "high":
            y -= 10
            pdf.setFont("Helvetica-Oblique", 9)
            pdf.drawString(
                60, y,
                "Note: These suggestions are supportive and do not replace medical treatment."
            )
            pdf.setFont("Helvetica", 11)

    y -= 40
    pdf.setFont("Helvetica-Oblique", 9)
    pdf.setFillColorRGB(1, 0, 0)
    pdf.drawString(
        50, y,
        "Disclaimer: This is an AI-based screening tool, not a medical diagnosis."
    )

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"prediction_{prediction_id}.pdf",
        mimetype="application/pdf"
    )


@reports_bp.route("/delete_prediction/<int:prediction_id>", methods=["POST"])
def delete_prediction(prediction_id):
    if not login_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM user_predictions
        WHERE id=%s AND user_id=%s
    """, (prediction_id, session["user_email"]))

    conn.commit()
    conn.close()

    flash("Prediction deleted successfully.", "success")
    return redirect(url_for("reports.account_history"))


# ======================================================
# PDF DOWNLOAD
# ======================================================
@reports_bp.route("/download_pdf")
def download_pdf():
    if not login_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT disease_type, input_data, probability, risk_level, timestamp
        FROM user_predictions
        WHERE user_id=%s
        ORDER BY timestamp DESC
        LIMIT 1
    """, (session["user_email"],))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return "No report available"

    disease, input_data, probability, risk, timestamp = row
    input_data = ast.literal_eval(input_data)
    probability = safe_float(probability)

    shap_explanation = session.get(
        "shap_explanation",
        "Clinical parameters influenced this prediction."
    )

    health_suggestions = session.get("health_suggestions")

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    y = 800

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(300, y, "AI Healthcare Screening Report")
    y -= 25

    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(
        300, y,
        f"Generated on: {datetime.now().strftime('%d %b %Y, %I:%M %p')}"
    )
    y -= 30

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, y, f"User: {session['user_email']}")
    y -= 18
    pdf.drawString(50, y, f"Disease: {disease.capitalize()}")
    y -= 30

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Input Parameters")
    y -= 20

    pdf.setFont("Helvetica", 11)
    for k, v in input_data.items():
        pdf.drawString(60, y, f"{k.replace('_', ' ').title()}: {v}")
        y -= 16

    y -= 20
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, f"Risk Level: {risk}")
    y -= 20
    pdf.drawString(50, y, f"Probability: {round(probability * 100, 2)}%")

    y -= 30
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Why this risk level?")
    y -= 18

    pdf.setFont("Helvetica", 11)
    wrapped_text = wrap(shap_explanation, 80)
    text_object = pdf.beginText(60, y)

    for line in wrapped_text:
        text_object.textLine(line)

    pdf.drawText(text_object)
    y -= 14 * len(wrapped_text)

    if health_suggestions:
        y -= 30
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, "Personalized Health Suggestions")
        y -= 18

        pdf.setFont("Helvetica", 11)

        title_line = f"{health_suggestions['title']} – {health_suggestions['message']}"
        for line in wrap(title_line, 80):
            pdf.drawString(60, y, line)
            y -= 14

        y -= 10

        for suggestion in health_suggestions["items"]:
            wrapped_lines = wrap(f"- {suggestion}", 75)
            for line in wrapped_lines:
                pdf.drawString(70, y, line)
                y -= 14

        if health_suggestions["level"] == "high":
            y -= 10
            pdf.setFont("Helvetica-Oblique", 9)
            pdf.drawString(
                60, y,
                "Note: These suggestions are supportive and do not replace medical treatment."
            )
            pdf.setFont("Helvetica", 11)

    y -= 40
    pdf.setFont("Helvetica-Oblique", 9)
    pdf.setFillColorRGB(1, 0, 0)
    pdf.drawString(
        50, y,
        "Disclaimer: This is an AI-based screening tool, not a medical diagnosis."
    )

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="health_report.pdf",
        mimetype="application/pdf"
    )


# ======================================================
# EXCEL DOWNLOAD
# ======================================================
@reports_bp.route("/download_excel")
def download_excel():
    if not login_required():
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT disease_type, input_data, probability, risk_level, timestamp
        FROM user_predictions
        WHERE user_id=%s
        ORDER BY timestamp DESC
        LIMIT 1
    """, (session["user_email"],))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return "No prediction found"

    df = pd.DataFrame([{
        "disease_type": row[0],
        "input_data": row[1],
        "probability": row[2],
        "risk_level": row[3],
        "timestamp": row[4],
    }])

    df["input_data"] = df["input_data"].apply(ast.literal_eval)
    df["probability (%)"] = df["probability"].apply(safe_float) * 100

    input_df = pd.json_normalize(df["input_data"])

    final_df = pd.concat(
        [
            df[["disease_type", "risk_level", "timestamp"]],
            input_df,
            df[["probability (%)"]]
        ],
        axis=1
    )

    buffer = io.BytesIO()
    final_df.to_excel(buffer, index=False)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="latest_health_prediction.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )