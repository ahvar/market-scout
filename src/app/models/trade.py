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
    profit_and_loss_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("profit_and_loss.id"), name="fk_profit_and_loss_id", index=True
    )
    profit_and_loss: so.Mapped["ProfitAndLoss"] = so.relationship(
        "ProfitAndLoss", back_populates="trades"
    )
