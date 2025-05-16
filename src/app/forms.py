from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    DateField,
    FloatField,
    TextAreaField,
)
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length
import sqlalchemy as sa
from src.app import db
from src.app.models.researcher import Researcher
from src.app.models.trade import Trade
from src.app.models.profit_and_loss import ProfitAndLoss


class LoginForm(FlaskForm):
    researcher_name = StringField(_l("Researcher Name"), validators=[DataRequired()])
    password = PasswordField(_l("Password"), validators=[DataRequired()])
    remember_me = BooleanField(_l("Remember Me"))
    submit = SubmitField(_l("Sign In"))


class ProfitAndLossForm(FlaskForm):
    name = StringField(_l("Profit & Loss Name"), validators=[DataRequired()])
    researcher = StringField(_l("Researcher"), validators=[DataRequired()])
    trades = StringField(_l("Start"), validators=[DataRequired()])


class RegistrationForm(FlaskForm):
    researcher_name = StringField(_l("Researcher Name"), validators=[DataRequired()])
    email = StringField(_l("Email"), validators=[DataRequired(), Email()])
    password = PasswordField(_l("Password"), validators=[DataRequired()])
    password2 = PasswordField(
        _l("Repeat Password"), validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField(_l("Register"))

    def validate_researcher_name(self, researcher_name):
        researcher = db.session.scalar(
            sa.select(Researcher).where(
                Researcher.researcher_name == researcher_name.data
            )
        )
        if researcher is not None:
            raise ValidationError(_l("Please use a different researcher name"))

    def validate_email(self, email):
        researcher = db.session.scalar(
            sa.select(Researcher).where(Researcher.email == email.data)
        )
        if researcher is not None:
            raise ValidationError(_l("Please use a different email address"))


class EditProfileForm(FlaskForm):
    researcher_name = StringField(_l("Researcher Name"), validators=[DataRequired()])
    about_me = TextAreaField(_l("About Me"), validators=[Length(min=0, max=140)])
    submit = SubmitField(_l("Submit"))

    def __init__(self, original_researcher_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_researcher_name = original_researcher_name

    def validate_username(self, researcher_name):
        if researcher_name.data != self.original_researcher_name:
            researcher = db.session.scalar(
                sa.select(Researcher).where(
                    Researcher.researcher_name == researcher_name.data
                )
            )
            if researcher is not None:
                raise ValidationError(_l("Please use a different researcher name"))


class PostForm(FlaskForm):
    post = TextAreaField(
        _l("Say something"), validators=[DataRequired(), Length(min=1, max=140)]
    )
    submit = SubmitField(_l("Submit"))


class EmptyForm(FlaskForm):
    submit = SubmitField(_l("Submit"))


class TradeForm(FlaskForm):
    date = DateField(_l("Expense Date"), validators=[DataRequired()])
    instrument_name = StringField(
        _l("Instrument (e.g. GBPUSD)"), validators=[DataRequired()]
    )
    product_type = StringField(
        _l("Leveraged Product (e.g. spot FX)"), validators=[DataRequired()]
    )
    trade = TextAreaField(_l("Order Details"))
    submit = SubmitField(_l("Submit"))


class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l("Email"), validators=[DataRequired(), Email()])
    submit = SubmitField(_l("Request Password Reset"))


class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l("Password"), validators=[DataRequired()])
    password2 = PasswordField(
        _l("Repeat Password"), validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField(_l("Request Password Reset"))
