from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
)
from werkzeug.security import generate_password_hash, check_password_hash
import time
import re

from extensions import mail
from flask_mail import Message

from services.db_utils import get_db_connection
from services.health_utils import (
    login_required,
    generate_otp,
    is_strong_password,
)

auth_bp = Blueprint("auth", __name__)


# ---------------- SIGNUP ----------------
@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]

        if not is_strong_password(password):
            flash(
                "Password must be at least 8 characters and include uppercase, lowercase, number, and special character.",
                "error",
            )
            return redirect(url_for("auth.signup"))

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            conn.close()
            flash("User already exists. Please login.", "error")
            return redirect(url_for("auth.login"))

        cursor.execute(
            "INSERT INTO users (email, password) VALUES (%s, %s)",
            (email, hashed_password),
        )

        conn.commit()
        conn.close()

        flash("Account created successfully! Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("signup.html")


# ---------------- LOGIN ----------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password, is_admin FROM users WHERE email=%s",
            (email,),
        )
        row = cursor.fetchone()
        conn.close()

        if row and check_password_hash(row[0], password):
            session["user_email"] = email
            session["is_admin"] = bool(row[1]) if row[1] is not None else False

            if session["is_admin"]:
                return redirect(url_for("admin.dashboard"))
            else:
                return redirect(url_for("main.dashboard"))

        flash("Invalid login credentials", "error")
        return redirect(url_for("auth.login"))

    return render_template("login.html")


# ---------------- PROFILE PAGE ----------------
@auth_bp.route("/profile")
def profile():
    if not login_required():
        return redirect(url_for("auth.login"))

    return render_template("profile.html", user=session["user_email"])


# ---------------- UPDATE EMAIL ----------------
@auth_bp.route("/update_email", methods=["POST"])
def update_email():
    if not login_required():
        return redirect(url_for("auth.login"))

    new_email = request.form["new_email"].strip()
    password = request.form["password"]

    if not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
        flash("Invalid email format.", "error")
        return redirect(url_for("auth.profile"))

    if new_email == session["user_email"]:
        flash("New email must be different from current email.", "error")
        return redirect(url_for("auth.profile"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT password FROM users WHERE email=%s",
        (session["user_email"],)
    )
    row = cursor.fetchone()

    if not row or not check_password_hash(row[0], password):
        conn.close()
        flash("Incorrect password.", "error")
        return redirect(url_for("auth.profile"))

    cursor.execute("SELECT 1 FROM users WHERE email=%s", (new_email,))
    if cursor.fetchone():
        conn.close()
        flash("Email already in use.", "error")
        return redirect(url_for("auth.profile"))

    cursor.execute(
        "UPDATE users SET email=%s WHERE email=%s",
        (new_email, session["user_email"]),
    )

    cursor.execute(
        "UPDATE user_predictions SET user_id=%s WHERE user_id=%s",
        (new_email, session["user_email"]),
    )

    conn.commit()
    conn.close()

    session.clear()
    flash("Email updated successfully. Please login again.", "success")
    return redirect(url_for("auth.login"))


# ---------------- UPDATE PASSWORD ----------------
@auth_bp.route("/update_password", methods=["POST"])
def update_password():
    if not login_required():
        return redirect(url_for("auth.login"))

    current_password = request.form["current_password"]
    new_password = request.form["new_password"]

    if not is_strong_password(new_password):
        flash("New password does not meet security requirements.", "error")
        return redirect(url_for("auth.profile"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT password FROM users WHERE email=%s",
        (session["user_email"],)
    )
    row = cursor.fetchone()

    if not row or not check_password_hash(row[0], current_password):
        conn.close()
        flash("Current password incorrect.", "error")
        return redirect(url_for("auth.profile"))

    hashed = generate_password_hash(new_password)
    cursor.execute(
        "UPDATE users SET password=%s WHERE email=%s",
        (hashed, session["user_email"]),
    )

    conn.commit()
    conn.close()

    session.clear()
    flash("Password updated successfully. Please login again.", "success")
    return redirect(url_for("auth.login"))


# ---------------- DELETE ACCOUNT ----------------
@auth_bp.route("/delete_account", methods=["POST"])
def delete_account():
    if not login_required():
        return redirect(url_for("auth.login"))

    password = request.form["password"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT password FROM users WHERE email=%s",
        (session["user_email"],)
    )
    row = cursor.fetchone()

    if not row or not check_password_hash(row[0], password):
        conn.close()
        flash("Password incorrect. Account not deleted.", "error")
        return redirect(url_for("auth.profile"))

    cursor.execute(
        "DELETE FROM user_predictions WHERE user_id=%s",
        (session["user_email"],),
    )

    cursor.execute(
        "DELETE FROM users WHERE email=%s",
        (session["user_email"],),
    )

    conn.commit()
    conn.close()

    session.clear()
    flash("Account deleted successfully.", "success")
    return redirect(url_for("main.home"))


# ---------------- FORGOT PASSWORD ----------------
@auth_bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"].strip()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        conn.close()

        if not user:
            flash("Email not registered.", "error")
            return redirect(url_for("auth.forgot_password"))

        otp = generate_otp()
        session["reset_email"] = email
        session["reset_otp"] = otp
        session["otp_expiry"] = time.time() + 300

        msg = Message(
            subject="Your Password Reset OTP",
            recipients=[email],
            body=f"Your OTP for password reset is: {otp}",
        )

        mail.send(msg)

        flash("OTP sent to your email.", "success")
        return redirect(url_for("auth.verify_otp"))

    return render_template("forgot_password.html")


@auth_bp.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        user_otp = request.form["otp"]

        if time.time() > session.get("otp_expiry", 0):
            flash("OTP has expired. Please request a new one.", "error")
            return redirect(url_for("auth.forgot_password"))

        if user_otp == session.get("reset_otp"):
            session.pop("reset_otp", None)
            session.pop("otp_expiry", None)
            return redirect(url_for("auth.reset_password"))
        else:
            flash("Invalid OTP.", "error")
            return redirect(url_for("auth.verify_otp"))

    return render_template("verify_otp.html")


@auth_bp.route("/resend_otp", methods=["POST"])
def resend_otp():
    email = session.get("reset_email")

    if not email:
        return redirect(url_for("auth.forgot_password"))

    otp = generate_otp()
    session["reset_otp"] = otp
    session["otp_expiry"] = time.time() + 300

    msg = Message(
        subject="Your New OTP",
        recipients=[email],
        body=f"Your new OTP is: {otp}",
    )
    mail.send(msg)

    flash("New OTP sent successfully.", "success")
    return redirect(url_for("auth.verify_otp"))


@auth_bp.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        new_password = request.form["password"]

        if not is_strong_password(new_password):
            flash("Password must meet strength requirements.", "error")
            return redirect(url_for("auth.reset_password"))

        hashed_password = generate_password_hash(new_password)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET password=%s WHERE email=%s",
            (hashed_password, session.get("reset_email")),
        )
        conn.commit()
        conn.close()

        session.pop("reset_email", None)
        session.pop("reset_otp", None)
        session.pop("otp_expiry", None)

        flash("Password updated successfully. Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html")


# ---------------- LOGOUT ----------------
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.home"))