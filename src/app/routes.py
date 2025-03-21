"""
NOTE:
    -------------------
    Decorator patterns:
    -------------------
    A common pattern with decorators is to use them to register functions as callbacks for certain
    events.

    -------------------
    Templates in Flask:
    -------------------
    Templates help achieve a separation between presentation and business logic. In Flask, templates
    are written as separate files, stored in a templates folder that is inside the application package.
    The render_template() function invokes the Jinja template engine that comes bundled with the Flask framework.
"""

from flask import render_template, flash, redirect, url_for, request
from urllib.parse import urlsplit
from flask_login import current_user, login_user, logout_user, login_required
from src.app import app, db
from src.app.forms import LoginForm, TradeForm, ProfitAndLossForm, RegistrationForm
from src.app.models.researcher import Researcher

import sqlalchemy as sa


@app.route("/")
@app.route("/index")
@login_required
def index():
    user = {"username": "Arthur"}
    pandl = [
        {
            "name": "Starter System",
            "researcher": {"username": "John"},
            "trades": [{"date": "2021-01-10", "contract": "contract"}],
            "contracts": [
                {"ticker": "AAPL", "price": 100, "description": "Apple Inc."}
            ],
        }
    ]
    return render_template("index.html", title="Home")


@app.route("/login", methods=["GET", "POST"])
def login():
    pandl_form = ProfitAndLossForm()
    trade_form = TradeForm()
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(Researcher).where(Researcher.username == form.username.data)
        )
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or urlsplit(next_page).netloc != "":
            next_page = url_for("index")
        # The argument to url_for() is the endpoint name, which is the name of the view function.
        return redirect(url_for(next_page))
    return render_template("login.html", title="Sign In", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = Researcher(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Congratulations, you are now a registered user!")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@app.route("/user/<username>")
@login_required
def user(username):
    user = db.first_or_404(sa.select(Researcher).where(Researcher.username == username))
    # pandl = user.pandl
    # trades = pandl.trades if pandl else []
    trades = [
        {"researcher": user, "instrument": "SPY"},
        {"researcher": user, "instrument": "AMZN"},
    ]
    return render_template("user.html", user=user, trades=trades)
