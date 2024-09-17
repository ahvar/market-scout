from typing import Optional

# an extension that provides a Flask-friendly wrapper to SQLAlchemy
import sqlalchemy as sa
import sqlalchemy.orm as so
from src.app import db
from datetime import datetime, timezone


class ProfitAndLoss(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(140))
    trades: so.Mapped["Trade"] = so.relationship("Trade", back_populates="owner")
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("user.id"), index=True)
    researcher: so.Mapped["User"] = so.relationship("User", back_populates="pandl")

    def __repr__(self) -> str:
        return "<Profit And Loss: {}>".format(self.name)
