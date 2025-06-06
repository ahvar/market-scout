from flask import request
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SubmitField,
    TextAreaField,
    SelectField,
    BooleanField,
    DateField,
)
from wtforms.validators import ValidationError, DataRequired, Length
import sqlalchemy as sa
from flask_babel import _, lazy_gettext as _l
from src.app import db
from src.app.models.researcher import Researcher


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


class StarterSystemForm(FlaskForm):
    instrument = SelectField(
        _l("Instrument"),
        choices=[
            ("GBPUSD", "GBPUSD"),
            ("EURUSD", "EURUSD"),
            ("USDJPY", "USDJPY"),
            ("AUDUSD", "AUDUSD"),
            ("USDCAD", "USDCAD"),
        ],
    )
    capital = SelectField(_l("Forecast Capital"), choices=[("100000", "100,000 USD")])
    fast_ewma = SelectField(
        _l("Fast EWMA (days)"), choices=[("16", "16"), ("32", "32")]
    )
    slow_ewma = SelectField(
        _l("Slow EWMA (days)"), choices=[("64", "64"), ("128", "128")]
    )
    days = SelectField(_l("Lookback Days"), choices=[("35", "35")])
    min_periods = SelectField(_l("Minimum Observations"), choices=[("10", "10")])
    vol_abs_min = SelectField(
        _l("Absolute Min Volatility"), choices=[("0.0000000001", "0.0000000001")]
    )
    vol_floor = BooleanField(_l("Apply Volatility Floor"), default=True)
    floor_min_quant = SelectField(
        _l("Floor Minimum Quantile"), choices=[("0.05", "0.05")]
    )
    submit = SubmitField(_l("Run Strategy"))


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


class ProfitAndLossForm(FlaskForm):
    name = StringField(_l("Profit & Loss Name"), validators=[DataRequired()])
    researcher = StringField(_l("Researcher"), validators=[DataRequired()])
    trades = StringField(_l("Start"), validators=[DataRequired()])


class SearchForm(FlaskForm):
    q = StringField(_l("Search"), validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if "formdata" not in kwargs:
            kwargs["formdata"] = request.args
        if "meta" not in kwargs:
            kwargs["meta"] = {"csrf": False}
        super(SearchForm, self).__init__(*args, **kwargs)
