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
from src.app import app
from src.app.forms import LoginForm, TradeForm, ProfitAndLossForm


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
    """
    login_form = LoginForm()
    pandl_form = ProfitAndLossForm()
    trade_form = TradeForm()
    if login_form.validate_on_submit():
        # The flash() function is a useful way to show a message to the user.
        flash(
            "Login requested from user {}, remember_me={}".format(
                login_form.username.data, login_form.remember_me.data
            )
        )
        # The argument to url_for() is the endpoint name, which is the name of the view function.
        return redirect(url_for("index"))
    return render_template("login.html", title="Sign In", form=login_form)
