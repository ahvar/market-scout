""" """

import os
import logging
from logging.handlers import SMTPHandler
from flask import Flask, request, current_app
from src.config import Config
from src.utils.helpers import init_frontend_logger
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_babel import Babel
from elasticsearch import Elasticsearch
from src.utils.helpers import init_frontend_logger


def get_locale():
    return request.accept_languages.best_match(current_app.config["LANGUAGES"])


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = "auth.login"
mail = Mail()
moment = Moment()
babel = Babel()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    babel.init_app(app)
    from src.app.errors import bp as errors_bp

    app.register_blueprint(errors_bp)
    from src.app.auth import bp as auth_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    from src.app.main import bp as main_bp

    app.register_blueprint(main_bp)
    from src.app.cli import bp as cli_bp

    app.register_blueprint(cli_bp)

    app.elasticsearch = (
        Elasticsearch([app.config["ELASTICSEARCH_URL"]])
        if app.config["ELASTICSEARCH_URL"]
        else None
    )
    if not app.debug and not app.testing:
        if app.config["MAIL_SERVER"]:
            auth = None
            if app.config["MAIL_USERNAME"] or app.config["MAIL_PASSWORD"]:
                auth = (app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
            secure = None
            if app.config["MAIL_USE_TLS"]:
                secure()
            mail_handler = SMTPHandler(
                mailhost=(app.config["MAIL_SERVER"], app.config["MAIL_PORT"]),
                fromaddr="no-reply@" + app.config["MAIL_SERVER"],
                toaddrs=app.config["ADMINS"],
                subject="Market Scout Failure",
                credentials=auth,
                secure=secure,
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)
    return app


app_logger = init_frontend_logger(logging.INFO)
from src.app.models import researcher, trade, profit_and_loss
