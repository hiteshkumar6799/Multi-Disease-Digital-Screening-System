from flask import Blueprint, render_template, redirect, url_for
from services.health_utils import login_required

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    return render_template("index.html")


@main_bp.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect(url_for("auth.login"))
    return render_template("dashboard.html")