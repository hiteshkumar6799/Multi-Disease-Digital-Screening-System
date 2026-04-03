import os
import psycopg2
import ast

from config import Config


def get_db_connection():
    """
    Helper to get a Postgres connection.
    This is exactly your old get_db_connection.
    """
    return psycopg2.connect(
        host=os.environ.get("PG_HOST", Config.PG_HOST),
        database=os.environ.get("PG_DB", Config.PG_DB),
        user=os.environ.get("PG_USER", Config.PG_USER),
        password=os.environ.get("PG_PASSWORD", Config.PG_PASSWORD),
        port=int(os.environ.get("PG_PORT", Config.PG_PORT))
    )


def get_float(form, field, default=0.0):
    """
    Safely extract a float from request.form.
    """
    try:
        return float(form.get(field, default))
    except Exception:
        return default


def safe_float(val):
    """
    Safe float cast used in Excel / PDF generation.
    """
    try:
        return float(val)
    except Exception:
        try:
            return float(val.decode(errors="ignore"))
        except Exception:
            return 0.0