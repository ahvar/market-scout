from flask import render_template
from flask_mail import Message
from src.app import mail, app


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)


def send_password_reset_email(researcher):
    token = researcher.get_reset_password_token()
    send_email(
        "[Market Scout] Reset Your Password",
        sender=app.config["ADMINS"][0],
        recipients=[researcher.email],
        text_body=render_template(
            "email/reset_password.txt", researcher=researcher, token=token
        ),
        html_body=render_template(
            "email/reset_password.html", researcher=researcher, token=token
        ),
    )
