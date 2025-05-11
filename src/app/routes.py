""" """

import logging
from datetime import datetime, timezone, UTC
from dateutil.relativedelta import relativedelta
from flask import render_template, flash, redirect, url_for, request
from urllib.parse import urlsplit
from flask_login import current_user, login_user, logout_user, login_required
from flask_babel import _
from flask import g
from flask_babel import get_locale
from src.app import app, db
from src.app.forms import (
    LoginForm,
    TradeForm,
    ProfitAndLossForm,
    RegistrationForm,
    EditProfileForm,
    EmptyForm,
    TradeForm,
    ResetPasswordRequestForm,
    ResetPasswordForm,
)
from src.app.models.researcher import Researcher, followers
from src.app.models.trade import Trade
from src.app.models.profit_and_loss import ProfitAndLoss
from src.app.email_service import send_password_reset_email
from src.utils.references import MKT_SCOUT_FRONTEND
import sqlalchemy as sa

frontend_logger = logging.getLogger(MKT_SCOUT_FRONTEND)


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
        flash(_("Your trade has been submitted!"))
        return redirect(url_for("index"))
    page = request.args.get("page", 1, type=int)
    own_trades_query = (
        sa.select(Trade)
        .join(ProfitAndLoss, Trade.profit_and_loss_id == ProfitAndLoss.id)
        .where(ProfitAndLoss.researcher_id == current_user.id)
        .where(Trade.open_date >= datetime.now(timezone.utc) - relativedelta(months=3))
        .order_by(Trade.open_date.desc())
    )
    following_page = request.args.get("following_page", 1, type=int)
    following_trades_query = (
        sa.select(Trade)
        .join(ProfitAndLoss, Trade.profit_and_loss_id == ProfitAndLoss.id)
        .join(followers, followers.c.followed_id == ProfitAndLoss.researcher_id)
        .where(followers.c.follower_id == current_user.id)
        .where(Trade.open_date >= datetime.now(timezone.utc) - relativedelta(months=3))
        .order_by(Trade.open_date.desc())
    )
    following_trades = db.paginate(
        following_trades_query,
        page=following_page,
        per_page=app.config["TRADES_PER_PAGE"],
        error_out=False,
    )
    own_trades = db.paginate(
        own_trades_query,
        page=page,
        per_page=app.config["TRADES_PER_PAGE"],
        error_out=False,
    )
    next_url = (
        url_for("index", page=own_trades.next_num) if own_trades.has_next else None
    )
    prev_url = (
        url_for("index", page=own_trades.prev_num) if own_trades.has_prev else None
    )
    following_next_url = (
        url_for("index", following_page=following_trades.next_num)
        if following_trades.has_next
        else None
    )
    following_prev_url = (
        url_for("index", following_page=following_trades.prev_num)
        if following_trades.has_prev
        else None
    )
    return render_template(
        "index.html",
        title="Home Page",
        form=form,
        own_trades=own_trades.items,
        following_trades=following_trades.items,
        next_url=next_url,
        prev_url=prev_url,
        following_next_url=following_next_url,
        following_prev_url=following_prev_url,
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
            flash(_("Invalid researcher name or password"))
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
        flash(_("Congratulations, you are now a registered!"))
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
        trades_query, page=page, per_page=app.config["TRADES_PER_PAGE"], error_out=False
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
        flash(_("Your changes have been saved"))
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
    g.locale = str(get_locale())


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
            flash(_("You cannot follow yourself!"))
            return redirect(url_for("researcher", researcher_name=researcher_name))
        current_user.follow(researcher_name)
        db.session.commit()
        flash(
            _("You are following %(researcher_name)s!", researcher_name=researcher_name)
        )
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
            flash(
                _(
                    "Researcher %(researcher_name)s is not found.",
                    researcher_name=researcher_name,
                )
            )
            return redirect(url_for("index"))
        if researcher == current_user:
            flash(_("You cannot unfollow yourself!"))
            return redirect(url_for("researcher", researcher_name=researcher_name))
        current_user.unfollow(researcher)
        db.session.commit()
        flash(
            _(
                "You are not following %(researcher_name)s",
                researcher_name=researcher_name,
            )
        )
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


@app.route("/reset_password_request", methods=["GET", "POST"])
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


@app.route("/reset_password/<token>", methods=["GET", "POST"])
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
