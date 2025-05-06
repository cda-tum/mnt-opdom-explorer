"""Nox sessions."""

from __future__ import annotations

import os
import shutil
from typing import TYPE_CHECKING

import nox

if TYPE_CHECKING:
    from collections.abc import Sequence


nox.needs_version = ">=2024.3.2"
nox.options.default_venv_backend = "uv"

nox.options.sessions = ["lint", "tests", "minimums"]

PYTHON_ALL_VERSIONS = ["3.10", "3.11", "3.12", "3.13"]

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
    # Arguments passed to uv install (e.g., --resolution)
    install_args: Sequence[str] = (),
    # Arguments passed directly to the pytest command
    pytest_args: Sequence[str] = (),
) -> None:
    """Installs dependencies and runs pytest using uv via session.install."""
    env = {"UV_PROJECT_ENVIRONMENT": session.virtualenv.location}

    # Install the current project. uv (as the backend) handles the installation.
    # Pass install_args for resolution strategy (e.g., lowest-direct).
    session.install(".", "--group", "test", *install_args)

    session.run(
        "pytest",
        *pytest_args,
        *session.posargs,
        "--cov-config=pyproject.toml",
        env=env,
    )


@nox.session(reuse_venv=True, python=PYTHON_ALL_VERSIONS)
def tests(session: nox.Session) -> None:
    """Run the test suite."""
    _run_tests(session)


@nox.session(reuse_venv=True, venv_backend="uv", python=PYTHON_ALL_VERSIONS)
def minimums(session: nox.Session) -> None:
    """Test the minimum versions of dependencies."""
    _run_tests(
        session,
        install_args=["--resolution=lowest-direct"],  # Passed to session.install
        pytest_args=["-Wdefault"],  # Passed to session.run("pytest", ...)
    )
    env = {"UV_PROJECT_ENVIRONMENT": session.virtualenv.location}
    session.run("uv", "tree", "--frozen", env=env)
    session.run("uv", "lock", "--refresh", env=env)
