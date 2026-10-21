"""Provided: remembers the IDs of resources you've created, per learner handle.

Agents, environments, and files are long-lived server-side resources: you
create them once and reuse them across many sessions. This tiny cache stores
their IDs locally so re-running the lab doesn't create duplicates.

Every resource is tagged with metadata {"workshop": "ma201", "owner": <handle>}
so learners sharing one API key (and cleanup.py) can tell theirs apart.
"""
from __future__ import annotations

import getpass
import json
import os
import re
import secrets
from pathlib import Path
from typing import Callable

STATE_FILE = Path(__file__).resolve().parent / ".ma201-state.json"


HANDLE_FILE = STATE_FILE.with_name(".ma201-handle")


def handle() -> str:
    """MA201_HANDLE if set; otherwise <os user>-<random suffix>, remembered locally.

    The suffix matters on shared machines (Codespaces, lab VMs) where everyone's
    OS user is the same and the API key is shared.
    """
    raw = os.environ.get("MA201_HANDLE")
    if not raw:
        try:
            raw = HANDLE_FILE.read_text().strip()
        except FileNotFoundError:
            raw = f"{getpass.getuser()}-{secrets.token_hex(2)}"
            HANDLE_FILE.write_text(raw)
    return re.sub(r"[^a-z0-9-]", "-", raw.lower())[:32]


def owner() -> dict:
    """Metadata to attach to everything you create."""
    return {"workshop": "ma201", "owner": handle()}


def _load() -> dict:
    try:
        return json.loads(STATE_FILE.read_text()).get(handle(), {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def get(key: str) -> str | None:
    return _load().get(key)


def put(key: str, value) -> None:
    try:
        data = json.loads(STATE_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    data.setdefault(handle(), {})[key] = value
    STATE_FILE.write_text(json.dumps(data, indent=2))


def sync(key: str, create: Callable[[], str]) -> str:
    """Return the cached ID for `key`, or call `create()` once and cache it."""
    existing = get(key)
    if existing:
        return existing
    new_id = create()
    put(key, new_id)
    return new_id


def forget(*keys: str) -> None:
    try:
        data = json.loads(STATE_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return
    for k in keys:
        data.get(handle(), {}).pop(k, None)
    STATE_FILE.write_text(json.dumps(data, indent=2))
