from typing import Optional

import sqlalchemy as sa
import sqlalchemy.orm as so
from src.app import db
from datetime import datetime, timezone
from src.app.models.researcher import Researcher


class ProfitAndLoss(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(140))
    trades: so.Mapped["Trade"] = so.relationship("Trade", back_populates="owner")
    #user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("user.id"), index=True)
    #researcher_id: so.Mapped[Researcher] = so.relationship("User", back_populates="pandl")
    researcher_id: so.Mapped[Researcher] = so.relationship(sa.ForeignKey(Researcher.id))

    def __repr__(self) -> str:
        return "<Profit And Loss: {}>".format(self.name)
