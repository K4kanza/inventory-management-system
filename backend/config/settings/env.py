"""Helpers for reading deployment configuration from the environment.

Kept separate from ``base.py`` so the environment modules (development,
production, vercel) can share one parsing strategy without ``base`` depending
on deployment concerns.
"""

import os


def env_list(name: str) -> list[str]:
    """Parse a comma-separated env var into a trimmed, de-duplicated list."""
    unique: dict[str, None] = {}
    for item in os.environ.get(name, "").split(","):
        value = item.strip()
        if value:
            unique.setdefault(value, None)
    return list(unique)


def csrf_origins(name: str = "CSRF_TRUSTED_ORIGINS") -> list[str]:
    """Parse ``CSRF_TRUSTED_ORIGINS`` into scheme + host entries.

    Django silently drops allow-list entries that carry no scheme, so accept a
    bare host (``6-9-sdd.vercel.app``) and upgrade it to ``https://`` rather than
    letting an operator wonder why the origin is not honoured.
    """
    origins = [value if "://" in value else f"https://{value}" for value in env_list(name)]
    # De-duplicate *after* normalising: "example.com" and "https://example.com"
    # are distinct entries going in but identical entries coming out.
    return list(dict.fromkeys(origins))
