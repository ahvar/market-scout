from typing import Optional
from flask_login import UserMixin
from src.app import login
from werkzeug.security import generate_password_hash, check_password_hash

# an extension that provides a Flask-friendly wrapper to SQLAlchemy
import sqlalchemy as sa
import sqlalchemy.orm as so
from src.app import db


class User(UserMixin, db.Model):
    """
    The User class created above will represent users stored in the database. The class inherits from db.Model,
    a base class for all models from Flask-SQLAlchemy. The User model defines several fields as class variables.
    These are the columns that will be created in the corresponding database table.

    Fields are assigned a type using Python type hints, wrapped with SQLAlchemy's so.Mapped generic type.
    A type declaration such as so.Mapped[int] or so.Mapped[str] define the type of the column,
    and also make values required, or non-nullable in database terms. To define a column that is allowed to be
    empty or nullable, the Optional helper from Python is also added, as password_hash demonstrates.
    """

    # column configured as primary key
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
    return db.session.get(User, int(id))
