"""
User Login Form

NOTE:
    -----------
    Extensions:
    -----------
    The four classes that represent the field types that I'm using for this form are imported directly from the WTForms package.
    Flask-WTF extension does not provide customized versions.

    -----------
    Validators:
    -----------
    The optional validators argument is used to attach validation behaviors to fields. The DataRequired validator checks that the
    field is not submitted empty.
    When you add any methods that match the pattern validate_<field_name>,
    WTForms takes those as custom validators and invokes them in addition
    to stock validators.

    -----------------
    Database Queries:
    -----------------
    Note how the two validation queries are issued. These queries will never find more than one result, so instead of running them
    with db.session.scalars() I'm using db.session.scalar() in singular, which returns None if there are no results, or else the
    first result.
"""

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
from src.app.models.user import User
from src.app.models.trade import Trade
from src.app.models.profit_and_loss import ProfitAndLoss


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class ProfitAndLossForm(FlaskForm):
    name = StringField("Profit & Loss Name", validators=[DataRequired()])
    researcher = StringField("Researcher", vaidators=[DataRequired()])
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
        user = db.session.scalar(sa.select(User).where(User.username == username.data))
        if user is not None:
            raise ValidationError("Please use a different username")

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError("Please use a different email address")
