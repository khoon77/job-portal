"""Utility helpers for loading Firebase service account credentials."""
from __future__ import annotations

import base64
import json
import os
from typing import Tuple

from firebase_admin import credentials

DEFAULT_CREDENTIALS_PATH = "job-portal-c9d7f-firebase-adminsdk-fbsvc-b0f6caa11d.json"


def _candidate_paths() -> Tuple[str, ...]:
    """Return candidate file paths to probe for the service account JSON."""
    env_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    default_path = DEFAULT_CREDENTIALS_PATH
    alt_env_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    paths = []
    for candidate in (env_path, alt_env_path, default_path):
        if candidate:
            expanded = os.path.expanduser(candidate)
            paths.append(os.path.abspath(expanded))
    return tuple(dict.fromkeys(paths))  # preserve order, remove duplicates


def load_firebase_credentials():
    """Load Firebase credentials from disk or FIREBASE_CREDENTIALS_BASE64.

    Returns
    -------
    tuple
        (credential, source_description) describing where the credential came from.

    Raises
    ------
    FileNotFoundError
        If no credential source is available.
    RuntimeError
        If the base64 payload exists but cannot be decoded/deserialised.
    """
    checked_sources = []

    # Prefer explicit file paths first for compatibility with existing workflow steps.
    for path in _candidate_paths():
        if os.path.exists(path):
            return credentials.Certificate(path), f"file:{path}"
        checked_sources.append(f"file:{path}")

    # Fallback to base64-encoded secret.
    encoded = os.getenv("FIREBASE_CREDENTIALS_BASE64", "").strip()
    if encoded:
        try:
            decoded = base64.b64decode(encoded)
            payload = json.loads(decoded.decode("utf-8"))
        except Exception as exc:  # noqa: BLE001 - provide context upstream
            raise RuntimeError("Failed to decode FIREBASE_CREDENTIALS_BASE64") from exc
        return credentials.Certificate(payload), "env:FIREBASE_CREDENTIALS_BASE64"

    # Nothing found; surface a clear error.
    tried = ", ".join(checked_sources) if checked_sources else "(no file paths checked)"
    raise FileNotFoundError(
        "Firebase credentials not found. Provide FIREBASE_CREDENTIALS_BASE64 or set "
        f"FIREBASE_CREDENTIALS_PATH. Tried: {tried}"
    )
