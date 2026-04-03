import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask secret key
    SECRET_KEY = os.environ.get("SECRET_KEY", "healthcare_project_secret")

    # Mail settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME')

    # 🔥 Render PostgreSQL (PRIMARY)
    DATABASE_URL = os.environ.get("DATABASE_URL")

    # 👇 Fallback for local development
    PG_HOST = os.environ.get("PG_HOST", "localhost")
    PG_DB = os.environ.get("PG_DB", "health_data")
    PG_USER = os.environ.get("PG_USER", "postgres")
    PG_PASSWORD = os.environ.get("PG_PASSWORD", "postgres")
    PG_PORT = int(os.environ.get("PG_PORT", 5432))