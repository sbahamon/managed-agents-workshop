"""Delete everything this lab created for YOUR handle. Run from lab/:

    .venv/bin/python cleanup.py --dry-run    # show what would be removed
    .venv/bin/python cleanup.py              # remove it

Only resources whose metadata says {"workshop": "ma201", "owner": <your handle>}
are touched, so it's safe on a shared API key. Safe to re-run.
"""
from __future__ import annotations

import argparse
import time

import state
from provided import client


def mine(obj) -> bool:
    md = getattr(obj, "metadata", None) or {}
    return md.get("workshop") == "ma201" and md.get("owner") == state.handle()


def attempt(label: str, fn) -> bool:
    try:
        fn()
        return True
    except Exception as exc:  # keep going: one stuck resource shouldn't block the rest
        print(f"    ! {label}: {type(exc).__name__}: {exc}")
        return False


def stop_session(session) -> None:
    """Interrupt a busy session and wait (briefly) until it's no longer running."""
    if session.status not in ("running", "rescheduling"):
        return
    attempt("interrupt", lambda: client.beta.sessions.events.send(
        session.id, events=[{"type": "user.interrupt"}]))
    for _ in range(15):  # status lags the interrupt event by a moment
        if client.beta.sessions.retrieve(session.id).status not in ("running", "rescheduling"):
            return
        time.sleep(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    dry = ap.parse_args().dry_run
    verb = "would remove" if dry else "removing"
    print(f"handle: {state.handle()}")

    agents = [a for a in client.beta.agents.list(limit=100, include_archived=True) if mine(a)]
    for agent in agents:
        for s in client.beta.sessions.list(agent_id=agent.id, limit=100, include_archived=True):
            if not mine(s):
                continue
            print(f"  {verb} session {s.id} ({s.status})")
            if not dry:
                stop_session(s)
                attempt(f"delete {s.id}", lambda: client.beta.sessions.delete(s.id))
        if agent.archived_at is None:
            print(f"  {verb} agent {agent.id} (archive)")
            if not dry:
                attempt(f"archive {agent.id}", lambda: client.beta.agents.archive(agent.id))

    for e in client.beta.environments.list(limit=100, include_archived=True):
        if mine(e):
            print(f"  {verb} environment {e.id}")
            if not dry and not attempt(f"delete {e.id}", lambda: client.beta.environments.delete(e.id)):
                attempt(f"archive {e.id}", lambda: client.beta.environments.archive(e.id))

    file_id = state.get("file_id")
    if file_id:
        print(f"  {verb} file {file_id}")
        if not dry:
            attempt(f"delete {file_id}", lambda: client.beta.files.delete(file_id))

    if not dry:
        state.forget("environment_id", "file_id", "agent_id")
        print("done. Local state cleared.")


if __name__ == "__main__":
    main()
