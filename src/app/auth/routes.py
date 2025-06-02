import logging
from flask import render_template, redirect, url_for, flash, request
from urllib.parse import urlsplit
from flask_login import login_user, logout_user, current_user
from flask_babel import _
import sqlalchemy as sa
from src.app import db
from src.app.auth import bp
from src.app.auth.forms import (
    LoginForm,
    RegistrationForm,
    ResetPasswordForm,
    ResetPasswordRequestForm,
)
from src.app.models.researcher import Researcher
from src.app.auth.email_service import send_password_reset_email
from src.utils.references import MKT_SCOUT_FRONTEND

frontend_logger = logging.getLogger(MKT_SCOUT_FRONTEND)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        researcher = db.session.scalar(
            sa.select(Researcher).where(
                Researcher.researcher_name == form.researcher_name.data
            )
        )
        if researcher is None or not researcher.check_password(form.password.data):
            flash(_("Invalid researcher name or password"))
            return redirect(url_for("login"))
        login_user(researcher, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or urlsplit(next_page).netloc != "":
            next_page = url_for("index")
        return redirect(next_page)
    return render_template("login.html", title="Sign In", form=form)


@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        researcher = Researcher(
            researcher_name=form.researcher_name.data, email=form.email.data
        )
        researcher.set_password(form.password.data)
        db.session.add(researcher)
        db.session.commit()
        flash(_("Congratulations, you are now a registered!"))
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@bp.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        researcher = db.session.scalar(
            sa.select(Researcher).where(Researcher.email == form.email.data)
        )
        if researcher:
            send_password_reset_email(researcher)
        flash(_("Check your email for the instructions to reset your password"))
        return redirect(url_for("login"))
    return render_template(
        "reset_password_request.html", title="Reset Password", form=form
    )


@bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    researcher = Researcher.verify_reset_password(token)
    if not researcher:
        return redirect(url_for("index"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        researcher.set_password(form.password.data)
        db.session.commit()
        flash(_("Your password has been reset"))
        return redirect(url_for("login"))
    return render_template("reset_password.html", form=form)
