"""REFERENCE SOLUTION for lab/agent.py. Try the stubs yourself first!

Run the app against this file with:  MA201_SOLUTION=1 uvicorn server:app
"""
from __future__ import annotations

from typing import Iterator, Optional

import state
from provided import (
    BUDGET_CENTS, ENV_PACKAGES, MODEL, MOUNT_PATH, SYSTEM, TOOLS,
    answer_custom_tool, client, needs_attention, pending_custom_tool_calls,
    turn_over, vendor_tarball,
)


# 1 ── Environment ────────────────────────────────────────────────────────────
def setup_environment() -> str:
    return state.sync("environment_id", lambda: client.beta.environments.create(
        name=f"vendor-vetting-{state.handle()}",
        config={
            "type": "cloud",
            "networking": {"type": "unrestricted"},
            "packages": ENV_PACKAGES,
        },
        metadata=state.owner(),
    ).id)


# 2 ── Files ──────────────────────────────────────────────────────────────────
def upload_vendor() -> str:
    return state.sync("file_id", lambda: client.beta.files.upload(
        file=("acme-csvkit.tar.gz", vendor_tarball(), "application/gzip"),
    ).id)


# 3 ── Agent ──────────────────────────────────────────────────────────────────
def setup_agent() -> str:
    return state.sync("agent_id", lambda: client.beta.agents.create(
        name=f"vendor-vetter-{state.handle()}",
        model=MODEL,
        system=SYSTEM,
        tools=TOOLS,
        metadata=state.owner(),
    ).id)


# 4 ── Session ────────────────────────────────────────────────────────────────
def start_vet(agent_id: str, env_id: str, file_id: str) -> str:
    session = client.beta.sessions.create(
        agent=agent_id,
        environment_id=env_id,
        title="Vet acme-csvkit",
        resources=[{"type": "file", "file_id": file_id, "mount_path": MOUNT_PATH}],
        metadata={**state.owner(), "target": "acme-csvkit"},
        budget={"type": "limit", "max_list_cost": {"amount": BUDGET_CENTS, "currency": "USD"}},
    )
    return session.id


# 5 ── Events: run a turn and close the custom-tool loop ───────────────────────
def run_vet(session_id: str, prompt: str) -> Iterator:
    with client.beta.sessions.events.stream(session_id) as stream:
        client.beta.sessions.events.send(session_id, events=[
            {"type": "user.message", "content": [{"type": "text", "text": prompt}]},
        ])
        for event in stream:
            yield event
            if event.type == "agent.custom_tool_use":
                answer_custom_tool(session_id, event)
            if turn_over(event):
                return


# 6 ── Find, don't create ─────────────────────────────────────────────────────
def find_open_session(agent_id: str) -> Optional[str]:
    for s in client.beta.sessions.list(agent_id=agent_id, order="desc", limit=20):
        if s.metadata.get("owner") == state.handle() and needs_attention(s):
            return s.id
    return None


# 7 ── Reattach: stream FIRST, then history, then live (deduped) ───────────────
def resume(session_id: str) -> Iterator:
    with client.beta.sessions.events.stream(session_id) as stream:
        history = list(client.beta.sessions.events.list(session_id, order="asc"))
        seen = {e.id for e in history}
        yield from history
        for call in pending_custom_tool_calls(history):
            answer_custom_tool(session_id, call)
        last_status = next((e for e in reversed(history) if e.type.startswith("session.status_")), None)
        if last_status and turn_over(last_status):
            return
        for event in stream:
            if event.id in seen:
                continue
            seen.add(event.id)
            yield event
            if event.type == "agent.custom_tool_use":
                answer_custom_tool(session_id, event)
            if turn_over(event):
                return


# 8 ── STRETCH: lock down the sandbox's network ────────────────────────────────
def lock_down(env_id: str) -> None:
    client.beta.environments.update(env_id, config={
        "type": "cloud",
        "networking": {"type": "limited", "allowed_hosts": [], "allow_package_managers": True},
    })


# 9 ── STRETCH: ship v2 without breaking v1 ────────────────────────────────────
def ship_v2(agent_id: str) -> int:
    current = client.beta.agents.retrieve(agent_id)
    updated = client.beta.agents.update(
        agent_id,
        version=current.version,
        system=SYSTEM + "\n\nPolicy v2: any undisclosed network call at install or import time "
                        "is an automatic `block` with risk_score >= 9.",
    )
    return updated.version
