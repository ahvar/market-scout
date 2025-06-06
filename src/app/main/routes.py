import logging
from pathlib import Path
from datetime import datetime, timezone
from dateutil import relativedelta
from flask import render_template, flash, redirect, url_for, request, g, current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
import sqlalchemy as sa
from langdetect import detect, LangDetectException
from src.app import db
from src.app.main.forms import (
    EmptyForm,
    PostForm,
    TradeForm,
    StarterSystemForm,
    EditProfileForm,
    SearchForm,
)
from src.app.models.researcher import Researcher, Post, ProfitAndLoss, Trade, followers
from src.app.translate import translate
from src.app.main import bp
from src.utils.references import MKT_SCOUT_FRONTEND

frontend_logger = logging.getLogger(MKT_SCOUT_FRONTEND)


@bp.route("/", methods=["GET", "POST"])
@bp.route("/index", methods=["GET", "POST"])
@login_required
def index():
    post_form = PostForm()
    if post_form.validate_on_submit():
        try:
            language = detect(form.post.data)
        except LangDetectException:
            language = ""

        post = Post(body=post_form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash(_("Your post is now live!"))
        return redirect(url_for("main.index"))
    # Set up page and pagination for posts
    page = request.args.get("page", 1, type=int)
    posts = db.paginate(
        current_user.following_posts(),
        page=page,
        per_page=current_app.config["POSTS_PER_PAGE"],
        error_out=False,
    )
    posts_next_url = (
        url_for("main.index", page=posts.next_num) if posts.has_next else None
    )
    posts_prev_url = (
        url_for("main.index", page=posts.prev_num) if posts.has_prev else None
    )
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
        return redirect(url_for("main.index"))
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
        per_page=current_app.config["TRADES_PER_PAGE"],
        error_out=False,
    )
    own_trades = db.paginate(
        own_trades_query,
        page=page,
        per_page=current_app.config["TRADES_PER_PAGE"],
        error_out=False,
    )
    next_url = (
        url_for("main.index", page=own_trades.next_num) if own_trades.has_next else None
    )
    prev_url = (
        url_for("main.index", page=own_trades.prev_num) if own_trades.has_prev else None
    )
    following_next_url = (
        url_for("main.index", following_page=following_trades.next_num)
        if following_trades.has_next
        else None
    )
    following_prev_url = (
        url_for("main.index", following_page=following_trades.prev_num)
        if following_trades.has_prev
        else None
    )
    return render_template(
        "index.html",
        title="Home Page",
        form=form,
        post_form=post_form,
        posts=posts,
        own_trades=own_trades.items,
        following_trades=following_trades.items,
        posts_next_url=posts_next_url,
        posts_prev_url=posts_prev_url,
        next_url=next_url,
        prev_url=prev_url,
        following_next_url=following_next_url,
        following_prev_url=following_prev_url,
    )


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
    g.locale = str(get_locale())


@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = str(get_locale())


@bp.route("/explore")
@login_required
def explore():
    page = request.args.get("page", 1, type=int)
    query = sa.select(Trade).order_by(Trade.open_date.desc())
    trades = db.paginate(
        query,
        page=page,
        per_page=current_app.config["TRADES_PER_PAGE"],
        error_out=False,
    )
    next_url = (
        url_for("main.explore", page=trades.next_num) if trades.has_next else None
    )
    prev_url = (
        url_for("main.explore", page=trades.prev_num) if trades.has_prev else None
    )
    return render_template(
        "explore.html",
        title=_("Explore Markets"),
        trades=trades.items,
        next_url=next_url,
        prev_url=prev_url,
    )


@bp.route("/find_more_researchers", methods=["GET", "POST"])
@login_required
def find_more_researchers():
    post_form = PostForm()
    if post_form.validate_on_submit():
        post = Post(body=post_form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash(_("Your post is now live!"))
        return redirect(url_for("main.find_more_researchers"))

    page = request.args.get("page", 1, type=int)
    posts = db.paginate(
        current_user.following_posts(),
        page=page,
        per_page=current_app.config["POSTS_PER_PAGE"],
        error_out=False,
    )
    posts_next_url = (
        url_for("main.find_more_researchers", page=posts.next_num)
        if posts.has_next
        else None
    )
    posts_prev_url = (
        url_for("main.find_more_researchers", page=posts.prev_num)
        if posts.has_prev
        else None
    )

    return render_template(
        "find_more_researchers.html",
        title=_("Research Community"),
        post_form=post_form,
        posts=posts,
        posts_next_url=posts_next_url,
        posts_prev_url=posts_prev_url,
    )


@bp.route("/researcher/<researcher_name>")
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
        per_page=current_app.config["TRADES_PER_PAGE"],
        error_out=False,
    )
    next_url = (
        url_for(
            "main.researcher",
            researcher_name=researcher.researcher_name,
            page=trades.next_num,
        )
        if trades.has_next
        else None
    )
    prev_url = (
        url_for(
            "main.researcher",
            researcher_name=researcher.researcher_name,
            page=trades.has_prev,
        )
        if trades.has_prev
        else None
    )
    # Get posts for this researcher
    posts_page = request.args.get("posts_page", 1, type=int)
    if researcher == current_user:
        # For the logged-in user, show their posts and posts from followed researchers
        posts = db.paginate(
            researcher.following_posts(),
            page=posts_page,
            per_page=current_app.config["POSTS_PER_PAGE"],
            error_out=False,
        )
    else:
        # For other researchers, show only their posts
        posts = db.paginate(
            sa.select(Post)
            .where(Post.researcher_id == researcher.id)
            .order_by(Post.timestamp.desc()),
            page=posts_page,
            per_page=current_app.config["POSTS_PER_PAGE"],
            error_out=False,
        )

    posts_next_url = (
        url_for(
            "main.researcher",
            researcher_name=researcher.researcher_name,
            posts_page=posts.next_num,
        )
        if posts.has_next
        else None
    )
    posts_prev_url = (
        url_for(
            "main.researcher",
            researcher_name=researcher.researcher_name,
            posts_page=posts.prev_num,
        )
        if posts.has_prev
        else None
    )
    form = EmptyForm()
    post_form = PostForm() if researcher == current_user else None
    return render_template(
        "researcher.html",
        researcher=researcher,
        trades=trades.items,
        next_url=next_url,
        prev_url=prev_url,
        form=form,
        posts=posts.items,
        posts_next_url=posts_next_url,
        posts_prev_url=posts_prev_url,
        post_form=post_form,
    )


@bp.route("/new_trade", methods=["GET", "POST"])
@login_required
def new_trade():
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
        return redirect(url_for("main.index"))

    return render_template("new_trade.html", title=_("New Trade"), form=form)


@bp.route("/follow/<researcher_name>", methods=["POST"])
@login_required
def follow(researcher_name):
    form = EmptyForm()
    if form.validate_on_submit():
        researcher = db.session.scalar(
            sa.select(Researcher).where(Researcher.researcher_name == researcher_name)
        )
        if researcher is None:
            flash(f"Researcher {researcher_name} not found.")
            return redirect(url_for("main.index"))
        if researcher == current_user:
            flash(_("You cannot follow yourself!"))
            return redirect(url_for("main.researcher", researcher_name=researcher_name))
        current_user.follow(researcher_name)
        db.session.commit()
        flash(
            _("You are following %(researcher_name)s!", researcher_name=researcher_name)
        )
        return redirect(url_for("main.researcher", researcher_name=researcher_name))
    else:
        return redirect(url_for("main.index"))


@bp.route("/unfollow/<researcher_name>", methods=["POST"])
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
            return redirect(url_for("main.index"))
        if researcher == current_user:
            flash(_("You cannot unfollow yourself!"))
            return redirect(url_for("main.researcher", researcher_name=researcher_name))
        current_user.unfollow(researcher)
        db.session.commit()
        flash(
            _(
                "You are not following %(researcher_name)s",
                researcher_name=researcher_name,
            )
        )
        return redirect(url_for("main.researcher", researcher_name=researcher_name))
    else:
        return redirect(url_for("main.index"))


@bp.route("/starter_system", methods=["GET", "POST"])
@login_required
def starter_system():
    form = StarterSystemForm()
    if form.validate_on_submit():
        instrument = form.instrument.data
        capital = float(form.capital.data)
        fast_ewma = int(form.fast_ewma.data)
        slow_ewma = int(form.slow_ewma.data)
        flash(_("Your strategy has been configured and is running!"))
        return redirect(url_for("main.index"))

    return render_template("starter_system.html", title=_("Starter System"), form=form)


@bp.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.researcher_name)
    if form.validate_on_submit():
        current_user.researcher_name = form.researcher_name.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_("Your changes have been saved"))
        return redirect(url_for("auth.edit_profile"))
    elif request.method == "GET":
        form.researcher_name.data = current_user.researcher_name
        form.about_me.data = current_user.about_me
    return render_template("edit_profile.html", title="Edit Profile", form=form)


@bp.route("/translate", methods=["POST"])
@login_required
def translate_text():
    """Translate text between languages.

    API endpoint that accepts JSON with source text, source language, and
    destination language. Uses the Azure Translator service to perform translation.

    Request body should be JSON with structure:
    {
        "text": "Text to translate",
        "source_language": "en",
        "dest_language": "es"
    }

    Returns:
        JSON response with the translated text:
        {
            "text": "Translated text here"
        }

    Requires authentication to prevent abuse of translation API quota.
    """
    data = request.get_json()
    return {
        "text": translate(data["text"], data["source_language"], data["dest_language"])
    }
