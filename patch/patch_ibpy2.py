import shutil
import subprocess
import os
from pathlib import Path


def generate_patch(original: Path, corrected: Path, patch: Path):
    """
    Generate a patch file from the difference between two files.
    """
    try:
        with open(patch, "w") as patch_out:
            subprocess.run(
                [
                    "diff",
                    "-u",
                    str(original),
                    str(corrected),
                ],
                check=True,
                stdout=patch_out,
                stderr=subprocess.DEVNULL,
            )
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            # diff found and written to patch file (expected)
            pass
        else:
            # re-raise the exception
            raise


def apply_patch(target: Path, patch_content: Path):
    """
    Apply a patch to a file.
    """
    # make a back-up if there isn't one
    backup_file = target.with_suffix(".bak")
    if not backup_file.exists:
        backup_file.touch()
        shutil.copy(target, backup_file)

    with open(patch_content, "r") as patch_file:
        patch_content = patch_file.read()

    # Apply the patch
    try:
        subprocess.run(
            ["patch", "-N", "-r", "-", str(target)],
            input=patch_content,
            text=True,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            pass
        else:
            raise
