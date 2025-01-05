"""Nox sessions."""

from __future__ import annotations

import os
import shutil
from typing import TYPE_CHECKING

import nox

if TYPE_CHECKING:
    from collections.abc import Sequence


nox.needs_version = ">=2024.3.2"
nox.options.default_venv_backend = "uv|virtualenv"


PYTHON_ALL_VERSIONS = ["3.9", "3.10", "3.11", "3.12"]

BUILD_REQUIREMENTS = [
    "setuptools>=66.1",
    "setuptools_scm>=8.1",
    "wheel>=0.40",
]

if os.environ.get("CI", None):
    nox.options.error_on_missing_interpreters = True


@nox.session(reuse_venv=True)
def lint(session: nox.Session) -> None:
    """Run the linter."""
    if shutil.which("pre-commit") is None:
        session.install("pre-commit")

    session.run("pre-commit", "run", "--all-files", *session.posargs, external=True)


def _run_tests(
    session: nox.Session,
    *,
    install_args: Sequence[str] = (),
    run_args: Sequence[str] = (),
    extras: Sequence[str] = (),
) -> None:
    posargs = list(session.posargs)
    env = {"PIP_DISABLE_PIP_VERSION_CHECK": "1"}

    extras_ = ["test", *extras]
    if "--cov" in posargs:
        extras_.append("coverage")
        posargs.append("--cov-config=pyproject.toml")

    session.install(*BUILD_REQUIREMENTS, *install_args, env=env)
    install_arg = f"-ve.[{','.join(extras_)}]"
    session.install("--no-build-isolation", install_arg, *install_args, env=env)
    session.run("pytest", *run_args, *posargs, env=env)


@nox.session(reuse_venv=True, python=PYTHON_ALL_VERSIONS)
def tests(session: nox.Session) -> None:
    """Run the test suite."""
    _run_tests(session)


@nox.session(reuse_venv=True, venv_backend="uv", python=PYTHON_ALL_VERSIONS)
def minimums(session: nox.Session) -> None:
    """Test the minimum versions of dependencies."""
    _run_tests(
        session,
        install_args=["--resolution=lowest-direct"],
        run_args=["-Wdefault"],
    )
    session.run("uv", "pip", "list")
