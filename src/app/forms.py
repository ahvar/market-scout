from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    DateField,
    FloatField,
    TextAreaField
)
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length
import sqlalchemy as sa
from src.app import db
from src.app.models.researcher import Researcher
from src.app.models.trade import Trade
from src.app.models.profit_and_loss import ProfitAndLoss


class LoginForm(FlaskForm):
    researcher_name = StringField("Researcher Name", validators=[DataRequired()])
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
    researcher_name = StringField("Researcher Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField(
        "Repeat Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Register")

    def validate_researcher_name(self, researcher_name):
        researcher = db.session.scalar(sa.select(Researcher).where(Researcher.researcher_name == researcher_name.data))
        if researcher is not None:
            raise ValidationError("Please use a different researcher name")

    def validate_email(self, email):
        researcher = db.session.scalar(sa.select(Researcher).where(Researcher.email == email.data))
        if researcher is not None:
            raise ValidationError("Please use a different email address")
        
class EditProfileForm(FlaskForm):
    researcher_name = StringField('Researcher Name', validators=[DataRequired()])
    about_me = TextAreaField('About Me', validators=[Length(min=0,max=140)])
    submit = SubmitField('Submit')
