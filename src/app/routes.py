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

from flask import render_template, flash, redirect, url_for
from flask_login import current_user, login_user
from src.app import app, db
from src.app.forms import LoginForm, TradeForm, ProfitAndLossForm
from src.app.models.user import User

import sqlalchemy as sa


@app.route("/")
@app.route("/index")
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
    return render_template("index.html", title="Home", user=user, pandl=pandl)


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    NOTE:
    ----------
    GET method
    ----------
    When the browser sends the GET request to receive the web page with the form, this method
    is going to return False, so in that case the function skips the if statement and goes
    directly to render the template in the last line of the function.

    ------------
    POST method
    ------------
    When the browser sends the POST request as a result of the user pressing the submit button,
    form.validate_on_submit() is going to gather all the data, run all the validators attached to fields,
    and if everything is all right it will return True

    -----------------
    Logging users in
    -----------------
    The current_user variable comes from the Flask-Login, and can be used at any time during the handling
    of a request to obtain the user object that represents the client of that request.
    """
    pandl_form = ProfitAndLossForm()
    trade_form = TradeForm()
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data)
        )
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        # The argument to url_for() is the endpoint name, which is the name of the view function.
        return redirect(url_for("index"))
    return render_template("login.html", title="Sign In", form=form)
