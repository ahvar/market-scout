from typing import Optional
from hashlib import md5
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from flask_login import UserMixin
from src.app import login
from werkzeug.security import generate_password_hash, check_password_hash

# an extension that provides a Flask-friendly wrapper to SQLAlchemy
import sqlalchemy as sa
import sqlalchemy.orm as so
from src.app import db

from src.app.models.trade import Trade
from src.app.models.profit_and_loss import ProfitAndLoss

followers = sa.Table(
    "followers",
    db.metadata,
    sa.Column(
        "follower_id", sa.Integer, sa.ForeignKey("researcher.id"), primary_key=True
    ),
    sa.Column(
        "followed_id", sa.Integer, sa.ForeignKey("researcher.id"), primary_key=True
    ),
)


class Researcher(UserMixin, db.Model):
    """ """

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    researcher_name: so.Mapped[str] = so.mapped_column(
        sa.String(64), index=True, unique=True
    )
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    pandl: so.Mapped[list["ProfitAndLoss"]] = so.relationship(
        "ProfitAndLoss", back_populates="researcher"
    )
    about_me: so.Mapped[Optional[str]] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    following: so.WriteOnlyMapped["Researcher"] = so.relationship(
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates="followers",
    )

    followers: so.WriteOnlyMapped["Researcher"] = so.relationship(
        secondary=followers,
        primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates="following",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return f"https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}"

    def __repr__(self):
        """
        How to print Researchers
        """
        return "<Researcher {}>".format(self.researcher_name)

    def follow(self, researcher):
        if not self.is_following(researcher):
            self.following.add(researcher)

    def unfollow(self, researcher):
        if self.is_following(researcher):
            self.following.remove(researcher)

    def is_following(self, researcher):
        query = self.following.select().where(Researcher.id == researcher.id)
        return db.session.scalar(query) is not None

    def followers_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.followers.select().subquery()
        )
        return db.session.scalar(query)

    def following_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.following.select().subquery()
        )
        return db.session.scalar(query)

    def following_profitability(self):
        """
        Returns a list of (researcher_id, researcher_name, total_pnl)
        for each researcher that self is following, for trades opened
        and closed within the last 3 months.
        """
        three_months_ago = datetime.now(timezone.utc) - relativedelta(months=3)

        return (
            sa.select(
                Researcher.id,
                Researcher.researcher_name,
                sa.func.sum(
                    sa.cast(Trade.close_price, sa.Numeric(12, 4))
                    - sa.cast(Trade.open_price, sa.Numeric(12, 4))
                ).label("total_pnl"),
            )
            .join(followers, followers.c.followed_id == Researcher.id, isouter=True)
            .join(ProfitAndLoss, ProfitAndLoss.researcher_id == Researcher.id)
            .join(Trade, Trade.profit_and_loss_id == ProfitAndLoss.id)
            .where(sa.or_(followers.c.follower_id == self.id, Researcher.id == self.id))
            .where(Trade.open_date >= three_months_ago)
            .where(Trade.close_date.isnot(None))
            .where(Trade.close_date >= three_months_ago)
            .group_by(Researcher.id, Researcher.researcher_name)
            .order_by(sa.desc("total_pnl"))
        )


@login.user_loader
def load_researcher(id):
    return db.session.get(Researcher, int(id))
