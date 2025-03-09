from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    DateField,
    FloatField,
)
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
import sqlalchemy as sa
from src.app import db
from src.app.models.researcher import Researcher
from src.app.models.trade import Trade
from src.app.models.profit_and_loss import ProfitAndLoss


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class ProfitAndLossForm(FlaskForm):
    name = StringField("Profit & Loss Name", validators=[DataRequired()])
    researcher = StringField("Researcher", validators=[DataRequired()])
    trades = StringField("Start", validators=[DataRequired()])


class TradeForm(FlaskForm):
    date = DateField("Expense Date", validators=[DataRequired()])
    owner = StringField("PandL Owner", validators=[DataRequired()])


class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField(
        "Repeat Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Register")

    def validate_username(self, username):
        user = db.session.scalar(sa.select(Researcher).where(Researcher.username == username.data))
        if user is not None:
            raise ValidationError("Please use a different username")

    def validate_email(self, email):
        user = db.session.scalar(sa.select(Researcher).where(Researcher.email == email.data))
        if user is not None:
            raise ValidationError("Please use a different email address")
