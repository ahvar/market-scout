import os
import click
from src.app import app


@app.cli.group()
def translate():
    """Translate and localization commands"""
    pass


@translate.command()
def update():
    if os.system("pybabel extract -F ../babel.cfg -k _l -o messages.pot ."):
        raise RuntimeError("extract command failed")
    if os.system("pybabel update -i messages.pot -d ./translations"):
        raise RuntimeError("update command failed")
    os.remove("messages.pot")


@translate.command()
def compile():
    if os.system("pybabel compile -d ./translations"):
        raise RuntimeError("compile command failed")


@translate.command()
@click.argument("lang")
def init(lang):
    """Initialize a new language"""
    if os.system("pybabel extract -F ../babel.cfg -k _l -o messages.pot ."):
        raise RuntimeError("extract command failed")
    if os.system("pybabel init -i messages.pot -d ./translations -l " + lang):
        raise RuntimeError("init command failed")
    os.remove("messages.pot")
