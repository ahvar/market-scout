"""
NOTE:
    The Flask application instance called "app" is imported from the package, also called "app"
"""

import sqlalchemy as sa
import sqlalchemy.orm as so
from src.app import app, db
from src.app.models.user import User
from src.app.models.profit_and_loss import ProfitAndLoss


@app.shell_context_processor
def make_shell_context():
    return {"sa": sa, "so": so, "db": db, "User": User, "Profit & Loss": ProfitAndLoss}
