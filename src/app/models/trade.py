from typing import Optional

# an extension that provides a Flask-friendly wrapper to SQLAlchemy
import sqlalchemy as sa
import sqlalchemy.orm as so
from src.app import db
from datetime import datetime, timezone


class Trade(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    open_date: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True),
        index=True,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    open_price: so.Mapped[float] = so.mapped_column(sa.Numeric(precision=12, scale=4), nullable=False)
    close_date: so.Mapped[datetime] = so.mapped_column(
        sa.DateTime(timezone=True),
        index=True,
        nullable=True
    )
    close_price: so.Mapped[float] = so.mapped_column(sa.Numeric(precision=12,scale=4), nullable=True)
    instrument_name: so.Mapped[str] = so.mapped_column(sa.String(50), index=True)
    product_type: so.Mapped[str] = so.mapped_column(sa.String(50), index=True)
    profit_and_loss_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey("profit_and_loss.id"), name="fk_profit_and_loss_id", index=True
    )
    profit_and_loss: so.Mapped["ProfitAndLoss"] = so.relationship(
        "ProfitAndLoss", back_populates="trades"
    )
