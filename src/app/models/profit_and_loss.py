from typing import Optional

import sqlalchemy as sa
import sqlalchemy.orm as so
from src.app import db
from datetime import datetime, timezone
from src.app.models.researcher import Researcher


class ProfitAndLoss(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(140))
    researcher_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("researcher.id"), name="fk_profit_and_loss_researcher_id", nullable=False)
    researcher: so.Mapped["Researcher"] = so.relationship("Researcher", back_populates="pandl")
    trades: so.Mapped[list["Trade"]] = so.relationship("Trade", back_populates="profit_and_loss")

    def __repr__(self) -> str:
        return "<Profit And Loss: {}>".format(self.name)
