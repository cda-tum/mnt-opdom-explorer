"""Utility module for accessing package metadata from pyproject.toml."""

from __future__ import annotations

import logging
from importlib.metadata import metadata

from mnt.ode._version import __version__

logger = logging.getLogger(__name__)


def get_package_metadata() -> dict[str, str | list[dict[str, str]]]:
    """Retrieves package metadata from the installed package.

    Returns:
        A dictionary containing package metadata including:
        - name: Application name
        - version: Application version
        - description: Short description
        - authors: List of author dictionaries with 'name' and 'email'
        - repository: GitHub repository URL
        - homepage: Project homepage URL
        - issues: Issue tracker URL
        - license: License name
        - license_url: URL to the license file
    """
    meta = metadata("mnt-ode")

    # Parse authors from metadata
    # Format can be: "Name1 <email1@example.com>, Name2 <email2@example.com>"
    authors = []
    author_emails = meta.get_all("Author-Email") or []
    for author_email_field in author_emails:
        # Split by ">, " to separate multiple authors (preserving email addresses)
        author_entries = author_email_field.split(">")
        for entry in author_entries:
            cleaned_entry = entry.strip().lstrip(",").strip()
            if "<" in cleaned_entry:
                name_part = cleaned_entry.split("<")[0].strip()
                email_part = cleaned_entry.split("<")[1].strip()
                if name_part and email_part:
                    authors.append({"name": name_part, "email": email_part})

    # Get project URLs
    repository = ""
    homepage = ""
    issues = ""

    project_urls = meta.get_all("Project-URL") or []
    for url_entry in project_urls:
        if ", " in url_entry:
            label, url = url_entry.split(", ", 1)
            if label == "Repository":
                repository = url
            elif label == "Homepage":
                homepage = url
            elif label == "Issues":
                issues = url

    # Get license information
    license_name = "Prosperity Public License 3.0.0"
    license_url = f"{repository}/blob/main/LICENSE.md" if repository else ""

    return {
        "name": meta.get("Name", "mnt-ode"),
        "version": __version__,
        "description": meta.get("Summary", "Explore Operational Domains of SiDB logic gates"),
        "authors": authors,
        "repository": repository,
        "homepage": homepage,
        "issues": issues,
        "license": license_name,
        "license_url": license_url,
    }


def get_app_display_name() -> str:
    """Gets the application display name.

    Returns:
        The human-readable application name.
    """
    return "MNT Operational Domain Explorer"


def get_organization_name() -> str:
    """Gets the organization name.

    Returns:
        The organization name.
    """
    return "Chair for Design Automation, Technical University of Munich (TUM), Germany"


def get_organization_domain() -> str:
    """Gets the organization domain.

    Returns:
        The organization domain.
    """
    return "cda.cit.tum.de"
