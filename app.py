from flask import Flask
from datetime import datetime

from config import Config
from extensions import mail


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    mail.init_app(app)

    @app.template_filter("fmt_datetime")
    def fmt_datetime(value):
        if not value:
            return ""

        if isinstance(value, str):
            value = value.strip()
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                try:
                    value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")
                    except ValueError:
                        return value

        return value.strftime("%d %b %Y, %I:%M %p")

    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.reports import reports_bp
    from routes.prediction import prediction_bp
    from routes.admin import admin

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(prediction_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin)

    return app


app = create_app()
from database.db_setup import init_db
init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)