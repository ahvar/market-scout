"""
"""
from datetime import datetime, timezone
from flask import render_template, flash, redirect, url_for, request
from urllib.parse import urlsplit
from flask_login import current_user, login_user, logout_user, login_required
from src.app import app, db
from src.app.forms import LoginForm, TradeForm, ProfitAndLossForm, RegistrationForm, EditProfileForm
from src.app.models.researcher import Researcher

import sqlalchemy as sa


@app.route("/")
@app.route("/index")
@login_required
def index():
    researcher = {"researcher_name": "Arthur"}
    pandl = [
        {
            "name": "Starter System",
            "researcher": {"researcher_name": "John"},
            "trades": [{"date": "2021-01-10", "contract": "contract"}],
            "contracts": [
                {"ticker": "AAPL", "price": 100, "description": "Apple Inc."}
            ],
        }
    ]
    return render_template("index.html", title="Home", pandl=pandl)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()
    if form.validate_on_submit():
        researcher = db.session.scalar(
            sa.select(Researcher).where(Researcher.researcher_name == form.researcher_name.data)
        )
        if researcher is None or not researcher.check_password(form.password.data):
            flash("Invalid researcher name or password")
            return redirect(url_for("login"))
        login_user(researcher, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or urlsplit(next_page).netloc != "":
            next_page = url_for("index")
        return redirect(next_page)
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
        researcher = Researcher(researcher_name=form.researcher_name.data, email=form.email.data)
        researcher.set_password(form.password.data)
        db.session.add(researcher)
        db.session.commit()
        flash("Congratulations, you are now a registered!")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@app.route("/researcher/<researcher_name>")
@login_required
def researcher(researcher_name):
    researcher = db.first_or_404(sa.select(Researcher).where(Researcher.researcher_name == researcher_name))
    # pandl = user.pandl
    # trades = pandl.trades if pandl else []
    trades = [
        {"researcher": researcher, "instrument": "SPY"},
        {"researcher": researcher, "instrument": "AMZN"},
    ]
    return render_template("researcher.html", researcher=researcher, trades=trades)

@app.route('/edit_profile', methods=['GET','POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.researcher_name = form.researcher_name.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.researcher_name.data = current_user.researcher_name
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
