import os
import psycopg2


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
conn.close()

print("✅ Database recreated successfully")
