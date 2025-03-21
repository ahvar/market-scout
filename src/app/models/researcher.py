from typing import Optional
from flask_login import UserMixin
from src.app import login
from werkzeug.security import generate_password_hash, check_password_hash

# an extension that provides a Flask-friendly wrapper to SQLAlchemy
import sqlalchemy as sa
import sqlalchemy.orm as so
from src.app import db


class Researcher(UserMixin, db.Model):
    """

    """
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    pandl: so.WriteOnlyMapped["ProfitAndLoss"] = so.relationship(
        "ProfitAndLoss", back_populates="researcher"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        """
        How to print Users
        """
        return "<User {}>".format(self.username)


@login.user_loader
def load_user(id):
    return db.session.get(Researcher, int(id))
