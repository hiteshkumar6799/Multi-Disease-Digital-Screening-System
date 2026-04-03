import os
import psycopg2


def get_db_connection():
    """
    Connect to PostgreSQL.
    Uses DATABASE_URL if available (Render),
    otherwise falls back to local PG_* variables.
    """

    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        return psycopg2.connect(database_url, sslmode="require")

    # Fallback for local development
    return psycopg2.connect(
        host=os.environ.get("PG_HOST", "localhost"),
        database=os.environ.get("PG_DB", "health_data"),
        user=os.environ.get("PG_USER", "postgres"),
        password=os.environ.get("PG_PASSWORD", "postgres"),
        port=int(os.environ.get("PG_PORT", 5432)),
    )


def init_db():
    """Create tables safely (call manually when needed)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # user_predictions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_predictions (
        id SERIAL PRIMARY KEY,
        user_id TEXT,
        disease_type TEXT,
        input_data TEXT,
        probability DOUBLE PRECISION,
        risk_level TEXT,
        shap_explanation TEXT,
        health_suggestions TEXT,
        model_used TEXT,
        model_accuracy DOUBLE PRECISION,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    cursor.close()
    conn.close()

    print("✅ Database initialized successfully")