"""
Reads and writes the project's .env file for the handful of DATABASE_*
keys that control which primary database (SQLite vs SQL Server) Django
connects to on its NEXT process start.

Deliberately does not touch any other .env content, and never mutates
the currently running process's os.environ — this is a "prepare for
next restart" control, not a live switch. Django reads DATABASES once
at process boot from config/settings/{development,production}.py, so
there is no safe way to hot-swap the app's own primary database
mid-process; the admin still has to restart the server (and migrate
any existing data themselves) for a change here to take effect.
"""
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"

DATABASE_KEYS = [
    "DATABASE_ENGINE", "DATABASE_NAME", "DATABASE_HOST", "DATABASE_PORT",
    "DATABASE_USER", "DATABASE_PASSWORD", "DATABASE_ODBC_DRIVER",
]


def read_database_env():
    """Returns {key: value} for the DATABASE_* keys currently in .env
    (empty string for any key not present)."""
    values = {key: "" for key in DATABASE_KEYS}
    if not ENV_PATH.exists():
        return values
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        key = key.strip()
        if key in values:
            values[key] = value.strip()
    return values


def write_database_env(updates):
    """Updates only the given {key: value} pairs in .env, preserving
    every other line (comments, blank lines, non-database keys) and
    their order. Appends a key at the end if it isn't already present."""
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines() if ENV_PATH.exists() else []
    seen = set()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, _ = stripped.partition("=")
        key = key.strip()
        if key in updates:
            lines[i] = f"{key}={updates[key]}"
            seen.add(key)
    for key, value in updates.items():
        if key not in seen:
            lines.append(f"{key}={value}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
