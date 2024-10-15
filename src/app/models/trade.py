from typing import Optional

# an extension that provides a Flask-friendly wrapper to SQLAlchemy
import sqlalchemy as sa
import sqlalchemy.orm as so
from src.app import db
from datetime import datetime, timezone


class Trade(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    date: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc)
    )
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("user.id"), index=True)
    owner_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("profit_and_loss.id"), index=True
    )
    owner: so.Mapped["ProfitAndLoss"] = so.relationship(
        "ProfitAndLoss", back_populates="trades"
    )
