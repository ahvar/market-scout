"""
"""
from datetime import datetime, timezone
from flask import render_template, flash, redirect, url_for, request
from urllib.parse import urlsplit
from flask_login import current_user, login_user, logout_user, login_required
from src.app import app, db
from src.app.forms import (
    LoginForm,
    TradeForm,
    ProfitAndLossForm,
    RegistrationForm,
    EditProfileForm,
    EmptyForm,
    TradeForm,
)
from src.app.models.researcher import Researcher
from src.app.models.trade import Trade
from src.app.models.profit_and_loss import ProfitAndLoss

import sqlalchemy as sa


@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
@login_required
def index():
    form = TradeForm()
    if form.validate_on_submit():
        pnl = db.session.scalar(
            sa.select(ProfitAndLoss).where(
                ProfitAndLoss.researcher_id == current_user.id
            )
        )
        if not pnl:
            pnl = ProfitAndLoss(
                name=f"{current_user.researcher_name}'s PnL",
                researcher_id=current_user.id,
            )
            db.session.add(pnl)
            db.session.commit()
        trade = Trade(
            open_date=form.date.data,
            instrument_name=form.instrument_name.data,
            product_type=form.product_type.data,
            open_price=0,  # or parse from form.trade.data if needed
            profit_and_loss_id=pnl.id,
        )
        db.session.add(trade)
        db.session.commit()
        flash("Your trade has been submitted!")
        return redirect(url_for("index"))
    page = request.args.get("page", 1, type=int)
    trades = db.paginate(
        current_user.following_profitability(),
        page=page,
        per_page=app.config["TRADES_PER_PAGE"],
        error_out=False,
    )
    next_url = url_for("index", page=trades.next_num) if trades.has_next else None
    prev_url = url_for("index", page=trades.prev_num) if trades.has_prev else None
    return render_template(
        "index.html",
        title="Home Page",
        form=form,
        trades=trades.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@app.route("/login", methods=["GET", "POST"])
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
        researcher = Researcher(
            researcher_name=form.researcher_name.data, email=form.email.data
        )
        researcher.set_password(form.password.data)
        db.session.add(researcher)
        db.session.commit()
        flash("Congratulations, you are now a registered!")
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@app.route("/researcher/<researcher_name>")
@login_required
def researcher(researcher_name):
    researcher = db.first_or_404(
        sa.select(Researcher).where(Researcher.researcher_name == researcher_name)
    )
    page = request.args.get("page", 1, type=int)
    trades_query = (
        sa.select(Trade)
        .join(ProfitAndLoss, Trade.profit_and_loss_id == ProfitAndLoss.id)
        .where(ProfitAndLoss.researcher_id == researcher.id)
        .order_by(Trade.open_date.desc())
    )
    trades = db.paginate(
        trades_query,
        page=page,
        per_page=app.config["POSTS_PER_PAGE"],
        error_out=False
    )
    next_url = (
        url_for(
            "researcher",
            researcher_name=researcher.researcher_name,
            page=trades.next_num,
        )
        if trades.has_next
        else None
    )
    prev_url = (
        url_for(
            "researcher",
            researcher_name=researcher.researcher_name,
            page=trades.has_prev,
        )
        if trades.has_prev
        else None
    )
    form = EmptyForm()
    return render_template(
        "researcher.html",
        researcher=researcher,
        trades=trades.items,
        next_url=next_url,
        prev_url=prev_url,
        form=form,
    )


@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.researcher_name)
    if form.validate_on_submit():
        current_user.researcher_name = form.researcher_name.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Your changes have been saved")
        return redirect(url_for("edit_profile"))
    elif request.method == "GET":
        form.researcher_name.data = current_user.researcher_name
        form.about_me.data = current_user.about_me
    return render_template("edit_profile.html", title="Edit Profile", form=form)


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()


@app.route("/follow/<researcher_name>", methods=["POST"])
@login_required
def follow(researcher_name):
    form = EmptyForm()
    if form.validate_on_submit():
        researcher = db.session.scalar(
            sa.select(Researcher).where(Researcher.researcher_name == researcher_name)
        )
        if researcher is None:
            flash(f"Researcher {researcher_name} not found.")
            return redirect(url_for("index"))
        if researcher == current_user:
            flash("You cannot follow yourself!")
            return redirect(url_for("researcher", researcher_name=researcher_name))
        current_user.follow(researcher_name)
        db.session.commit()
        flash(f"You are following {researcher_name}!")
        return redirect(url_for("researcher", researcher_name=researcher_name))
    else:
        return redirect(url_for("index"))


@app.route("/unfollow/<researcher_name>", methods=["POST"])
@login_required
def unfollow(researcher_name):
    form = EmptyForm()
    if form.validate_on_submit():
        researcher = db.session.scalar(
            sa.select(Researcher).where(Researcher.researcher_name == researcher_name)
        )
        if researcher is None:
            flash(f"Researcher {researcher_name} is not found.")
            return redirect(url_for("index"))
        if researcher == current_user:
            flash("You cannot unfollow yourself!")
            return redirect(url_for("researcher", researcher_name=researcher_name))
        current_user.unfollow(researcher)
        db.session.commit()
        flash(f"You are not following {researcher_name}")
        return redirect(url_for("researcher", researcher_name=researcher_name))
    else:
        return redirect(url_for("index"))


@app.route("/explore")
@login_required
def explore():
    page = request.args.get("page", 1, type=int)
    query = sa.select(Trade).order_by(Trade.open_date.desc())
    trades = db.paginate(
        query, page=page, per_page=app.config["TRADES_PER_PAGE"], error_out=False
    )
    next_url = url_for("explore", page=trades.next_num) if trades.has_next else None
    prev_url = url_for("explore", page=trades.prev_num) if trades.has_prev else None
    return render_template(
        "index.html",
        title="Explore",
        trades=trades.items,
        next_url=next_url,
        prev_url=prev_url,
    )
