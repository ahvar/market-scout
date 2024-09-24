import shutil
import subprocess
import os
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent


def generate_ibpy2_init_patch():
    original_file = project_root / "src" / "patch" / "ibpy2_original_init.py"
    modified_file = project_root / "src" / "patch" / "ibpy2_modified_init.py"
    patch_file = project_root / "src" / "patch" / "fix_syntax_error.patch"

    # Generate the patch file
    try:
        with open(patch_file, "w") as patch_out:
            subprocess.run(
                ["diff", "-u", str(original_file), str(modified_file)],
                check=True,
                stdout=patch_out,
            )
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            # diff found and written to patch file (expected behavior)
            pass
        else:
            # re-raise the exception
            raise


def apply_ibpy2_init_patch():
    # Get the path to ibpy2 init
    ibpy2_init_filepath = (
        project_root
        / "envs"
        / "lib"
        / "python3.11"
        / "site-packages"
        / "ib"
        / "lib"
        / "__init__.py"
    )

    # Make a backup
    ibpy2_path_backup = ibpy2_init_filepath.with_suffix(".bak")
    shutil.copy(ibpy2_init_filepath, ibpy2_path_backup)

    # Read the patch file
    try:
        with open(
            project_root / "src" / "patch" / "fix_syntax_error.patch", "r"
        ) as patch_in:
            patch_content = patch_in.read()

        # Apply the patch
        subprocess.run(
            [
                "patch",
                str(ibpy2_init_filepath),
            ],
            input=patch_content,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            pass
        else:
            raise


if __name__ == "__main__":
    apply_ibpy2_init_patch()
