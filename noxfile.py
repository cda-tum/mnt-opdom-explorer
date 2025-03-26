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

PYTHON_VERSIONS = ["3.10", "3.11", "3.12", "3.13"]
BUILD_REQS = ["hatchling>=1.27.0", "hatch-vcs>=0.4.0", "editables>=0.3.0"]

if os.getenv("CI"):
    nox.options.error_on_missing_interpreters = True


@nox.session(reuse_venv=True)
def lint(session: nox.Session) -> None:
    """Run the linter."""
    session.install("pre-commit") if not shutil.which("pre-commit") else None
    session.run("pre-commit", "run", "--all-files", *session.posargs, external=True)


def _run_tests(
    session: nox.Session,
    *,
    install_args: Sequence[str] = (),
    run_args: Sequence[str] = (),
    extras: Sequence[str] = (),
) -> None:
    env = {"PIP_DISABLE_PIP_VERSION_CHECK": "1"}
    posargs = list(session.posargs)  # Convert to list for mutability

    if "--cov" in posargs:
        extras = (*extras, "coverage")  # Use tuple concatenation
        posargs.append("--cov-config=pyproject.toml")

    session.run("python", "--version", external=True)
    session.run("uv", "--version", external=True, env=env)

    session.run("uv", "pip", "install", *BUILD_REQS, *install_args, env=env)

    sync_args = ["uv", "sync", "--extra", "test", "--reinstall", "--active"]

    session.run(*sync_args, *install_args, env=env)

    session.run("uv", "pip", "install", "-e", ".", *install_args, env=env)

    session.run("uv", "pip", "list", env=env)

    session.run("pytest", "--rootdir=.", *run_args, *posargs, external=True, env=env)


@nox.session(python=PYTHON_VERSIONS, reuse_venv=True)
def tests(session: nox.Session) -> None:
    """Run the test suite."""
    _run_tests(session)


@nox.session(python=PYTHON_VERSIONS, reuse_venv=True)
def minimums(session: nox.Session) -> None:
    """Test with minimum dependency versions."""
    _run_tests(
        session,
        install_args=["--resolution=lowest-direct"],
        run_args=["-Wdefault"],
    )
    session.run("uv", "pip", "list")
