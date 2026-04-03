import json
import os
import psycopg2


# Optional: keep this constant name, though we no longer use a .db file
DB_PATH = "database/health_data.db"


def get_db_connection():
    """
    Create and return a PostgreSQL connection using environment variables:
    PG_HOST, PG_DB, PG_USER, PG_PASSWORD, PG_PORT
    """
    return psycopg2.connect(
        host=os.environ.get("PG_HOST", "localhost"),
        database=os.environ.get("PG_DB", "health_data"),
        user=os.environ.get("PG_USER", "postgres"),
        password=os.environ.get("PG_PASSWORD", "postgres"),
        port=int(os.environ.get("PG_PORT", 5432)),
    )


def save_prediction(
    user_id,
    disease_type,
    input_data,
    probability,
    risk_level,
    shap_explanation,
    health_suggestions,
    model_accuracy,
):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO user_predictions (
            user_id,
            disease_type,
            input_data,
            probability,
            risk_level,
            shap_explanation,
            health_suggestions,
            model_used,
            model_accuracy
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            user_id,
            disease_type,
            json.dumps(input_data),
            probability,
            risk_level,
            shap_explanation,
            json.dumps(health_suggestions),
            "XGBoost",
            model_accuracy,
        ),
    )

    conn.commit()
    cursor.close()
    conn.close()


# ----------------------------------------------------------------------
#                          ADMIN HELPER FUNCTIONS
# ----------------------------------------------------------------------
# Assumes you have:
#   users(id, email, is_active, is_admin, created_at)
#   user_predictions(id, user_id, disease_type, input_data, probability,
#                    risk_level, shap_explanation, health_suggestions,
#                    model_used, model_accuracy, timestamp)
# ----------------------------------------------------------------------


# ---------- ADMIN: USERS ----------


def get_all_users():
    """
    Return all users as list of tuples:
    (id, email, is_active, is_admin, created_at)
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, email, is_active, is_admin, created_at
        FROM users
        ORDER BY created_at DESC
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def toggle_user_active(user_id: int) -> bool:
    """
    Flip is_active for the given user.
    Returns True if user existed and was updated, False otherwise.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT is_active FROM users WHERE id = %s", (user_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return False

    new_status = not row[0]
    cur.execute(
        "UPDATE users SET is_active = %s WHERE id = %s",
        (new_status, user_id),
    )
    conn.commit()
    cur.close()
    conn.close()
    return True


def delete_user(user_id: int):
    """
    Permanently delete a user.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()


def count_users() -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]
    cur.close()
    conn.close()
    return total


# ---------- ADMIN: PREDICTIONS (existing) ----------


def count_predictions() -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM user_predictions")
    total = cur.fetchone()[0]
    cur.close()
    conn.close()
    return total


def count_predictions_by_risk(risk_level: str) -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM user_predictions WHERE risk_level = %s",
        (risk_level,),
    )
    total = cur.fetchone()[0]
    cur.close()
    conn.close()
    return total


def get_latest_predictions(limit: int = 10):
    """
    Returns rows as:
    (id, user_email, disease_type, risk_level, probability, timestamp)
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT p.id,
               u.email,
               p.disease_type,
               p.risk_level,
               p.probability,
               p.timestamp
        FROM user_predictions p
        LEFT JOIN users u ON p.user_id = u.email
        ORDER BY p.timestamp DESC
        LIMIT %s
        """,
        (limit,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_all_predictions_with_filters(
    disease_type=None,
    risk_level=None,
    date_from=None,
    date_to=None,
    limit: int = 200,
):
    """
    Returns rows as:
    (id, user_email, disease_type, risk_level, probability, timestamp)
    Filters are all optional.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    query = """
        SELECT p.id,
               u.email,
               p.disease_type,
               p.risk_level,
               p.probability,
               p.timestamp
        FROM user_predictions p
        LEFT JOIN users u ON p.user_id = u.email
        WHERE 1 = 1
    """
    params = []

    if disease_type:
        query += " AND p.disease_type = %s"
        params.append(disease_type)

    if risk_level:
        query += " AND p.risk_level = %s"
        params.append(risk_level)

    if date_from:
        query += " AND p.timestamp >= %s"
        params.append(date_from)

    if date_to:
        query += " AND p.timestamp <= %s"
        params.append(date_to)

    query += " ORDER BY p.timestamp DESC LIMIT %s"
    params.append(limit)

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_all_disease_types():
    """
    Return distinct disease_type values from user_predictions.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT disease_type FROM user_predictions ORDER BY disease_type")
    diseases = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return diseases


def get_all_predictions_for_csv():
    """
    Return all prediction rows for CSV export as:
    (id, user_email, disease_type, risk_level, probability, timestamp)
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT p.id,
               u.email,
               p.disease_type,
               p.risk_level,
               p.probability,
               p.timestamp
        FROM user_predictions p
        LEFT JOIN users u ON p.user_id = u.email
        ORDER BY p.timestamp DESC
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# ---------- ADMIN ANALYTICS: NEW FUNCTIONS ----------


def count_predictions_today() -> int:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM user_predictions WHERE DATE(timestamp) = CURRENT_DATE"
    )
    total = cur.fetchone()[0]
    cur.close()
    conn.close()
    return total


def count_new_users_today() -> int:
    """
    Returns number of users created today.
    If your users table does not have created_at, you can temporarily
    return 0 instead and remove the query.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT COUNT(*) FROM users WHERE DATE(created_at) = CURRENT_DATE"
        )
        total = cur.fetchone()[0]
    except psycopg2.Error:
        total = 0
    cur.close()
    conn.close()
    return total


def get_most_predicted_disease():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT disease_type, COUNT(*) AS total
        FROM user_predictions
        GROUP BY disease_type
        ORDER BY total DESC
        LIMIT 1
        """
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None


def get_disease_distribution():
    """
    Returns list of (disease_type, count)
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT disease_type, COUNT(*) AS total
        FROM user_predictions
        GROUP BY disease_type
        ORDER BY total DESC
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_risk_distribution():
    """
    Returns list of (risk_level, count)
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT risk_level, COUNT(*) AS total
        FROM user_predictions
        GROUP BY risk_level
        ORDER BY total DESC
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_predictions_trend():
    """
    Returns list of (date, count) for predictions per day.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT DATE(timestamp) AS day, COUNT(*) AS total
        FROM user_predictions
        GROUP BY DATE(timestamp)
        ORDER BY day ASC
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_top_active_users(limit: int = 5):
    """
    Returns list of (user_id, count) ordered by prediction count desc.
    user_id here is the value stored in user_predictions.user_id
    (in your case, email).
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT user_id, COUNT(*) AS total
        FROM user_predictions
        GROUP BY user_id
        ORDER BY total DESC
        LIMIT %s
        """,
        (limit,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_latest_high_risk_predictions(limit: int = 5):
    """
    Returns latest high-risk predictions as tuples:
    (id, user_id, disease_type, probability, risk_level, timestamp)
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, user_id, disease_type, probability, risk_level, timestamp
        FROM user_predictions
        WHERE risk_level = 'High Risk'
        ORDER BY timestamp DESC
        LIMIT %s
        """,
        (limit,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_high_risk_trend():
    """
    Returns list of (date, count) for high-risk predictions per day.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT DATE(timestamp) AS day, COUNT(*) AS total
        FROM user_predictions
        WHERE risk_level = 'High Risk'
        GROUP BY DATE(timestamp)
        ORDER BY day ASC
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_avg_probability_by_disease():
    """
    Returns list of (disease_type, avg_probability)
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT disease_type, ROUND(AVG(probability)::numeric, 2) AS avg_prob
        FROM user_predictions
        GROUP BY disease_type
        ORDER BY avg_prob DESC
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_high_risk_by_disease():
    """
    Returns list of (disease_type, count) for only high-risk cases.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT disease_type, COUNT(*) AS total
        FROM user_predictions
        WHERE risk_level = 'High Risk'
        GROUP BY disease_type
        ORDER BY total DESC
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# ----------------------------------------------------------------------
#                          MANUAL TEST (optional)
# ----------------------------------------------------------------------


if __name__ == "__main__":
    sample_input = {
        "age": 52,
        "bp": 140,
        "glucose": 180,
    }

    sample_suggestions = {
        "level": "high",
        "title": "High Risk Detected",
        "message": "Consult doctor immediately",
        "items": ["Reduce sugar", "Exercise daily"],
    }

    save_prediction(
        user_id="user_001",
        disease_type="diabetes",
        input_data=sample_input,
        probability=0.87,
        risk_level="High Risk",
        shap_explanation="High glucose and age are major contributors.",
        health_suggestions=sample_suggestions,
        model_accuracy=90.16,
    )

    print("Sample prediction saved to database")