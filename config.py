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

    # 🔥 Database configuration
    DATABASE_URL = os.environ.get("DATABASE_URL")

    if DATABASE_URL:
        # Fix Render postgres:// issue
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # 👇 Local PostgreSQL fallback
        PG_HOST = os.environ.get("PG_HOST", "localhost")
        PG_DB = os.environ.get("PG_DB", "health_data")
        PG_USER = os.environ.get("PG_USER", "postgres")
        PG_PASSWORD = os.environ.get("PG_PASSWORD", "postgres")
        PG_PORT = int(os.environ.get("PG_PORT", 5432))

        SQLALCHEMY_DATABASE_URI = (
            f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False