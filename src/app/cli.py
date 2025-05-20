import click
import os
from pathlib import Path
from src.app import app


@app.cli.group()
def translate():
    """Translate and localization commands"""
    pass


@translate.command()
def update():
    project_root = Path(__file__).resolve().parent.parent.parent
    babel_cfg = project_root / "src" / "babel.cfg"
    pot_file = project_root / "src" / "messages.pot"
    translations_dir = project_root / "src" / "app" / "translations"
    extract_cmd = (
        f"pybabel extract -F {babel_cfg} -k _l -k _ -o {pot_file} {project_root}"
    )
    if os.system(extract_cmd):
        raise RuntimeError("Extract command failed")
    update_cmd = f"pybabel update -i {pot_file} -d {translations_dir}"
    if os.system(update_cmd):
        raise RuntimeError("Update command failed")

    if pot_file.exists():
        pot_file.unlink()


@translate.command()
def compile():
    project_root = Path(__file__).resolve().parent.parent.parent
    translations_dir = project_root / "src" / "app" / "translations"
    if os.system(f"pybabel compile -d {translations_dir}"):
        raise RuntimeError("Compile command failed")


@translate.command()
@click.argument("lang")
def init(lang):
    """Initialize a new language"""
    project_root = Path(__file__).resolve().parent.parent.parent
    babel_cfg = project_root / "src" / "babel.cfg"
    pot_file = project_root / "src" / "messages.pot"
    translations_dir = project_root / "src" / "app" / "translations"

    print(f"Extracting strings using config: {babel_cfg}")
    extract_cmd = (
        f"pybabel extract -F {babel_cfg} -k _l -k _ -o {pot_file} {project_root}"
    )
    if os.system(extract_cmd):
        raise RuntimeError("Extract command failed")

    print(f"Initializing language {lang} in: {translations_dir}")
    init_cmd = f"pybabel init -i {pot_file} -d {translations_dir} -l {lang}"
    if os.system(init_cmd):
        raise RuntimeError("Init command failed")

    if pot_file.exists():
        print(f"Removing temporary file: {pot_file}")
        pot_file.unlink()
