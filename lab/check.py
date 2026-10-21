"""Checkpoints. Run from lab/ with the venv's Python (.venv/bin/python check.py ...):

    python check.py              # run checkpoints 0-5 and 6–7 in order, stop at the first failure
    python check.py --step 3     # run one checkpoint
    python check.py --step 7     # stubs 6 + 7 together (same as --step 6)
    python check.py --step 8     # stretch: lock down networking
    python check.py --step 9     # stretch: ship v2, prove v1 is pinned
    python check.py --solution   # run against solutions/agent.py instead of your agent.py

Steps 5-7 start real sessions (about 1 minute and a few cents each; 6/7 take 2-4 min).
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import sys
import threading
import time

import state
from provided import VERDICT_DIR, VET_PROMPT, client

GREEN, RED, DIM, END = "\033[32m", "\033[31m", "\033[2m", "\033[0m"


class Fail(Exception):
    pass


def ok(msg):
    print(f"  {GREEN}✓{END} {msg}")


def need(cond, msg):
    if not cond:
        raise Fail(f"expected: {msg}")
    ok(msg)


def drain(events, label, stop_after=None, timeout=420, stuck_hint=None, quiet=None, stall_note=None):
    """Consume an event iterator, printing a compact trace. Returns the events seen.

    A silent stream never reaches the timeout check below, so a watchdog prints
    `stuck_hint` after 90 s with no events and gives up after `quiet` silent seconds,
    printing `stall_note` (a neutral ⏸ line) instead of a red ✗ when the silence is expected.
    """
    quiet = quiet or timeout
    seen, t0 = [], time.time()
    last = [time.time()]
    done = threading.Event()

    def watchdog():
        hinted = False
        while not done.wait(5):
            silent = time.time() - last[0]
            if stuck_hint and not hinted and silent > 90:
                print(f"    {DIM}no events for {silent:.0f}s. {stuck_hint}{END}", flush=True)
                hinted = True
            if silent > quiet:
                if stall_note:
                    print(f"  ⏸ {label}: no events for {quiet}s. {stall_note}", flush=True)
                else:
                    print(f"  {RED}✗ {label}: no events for {quiet}s. {stuck_hint or ''}{END}", flush=True)
                os._exit(1)

    threading.Thread(target=watchdog, daemon=True).start()
    try:
        return _drain(events, label, stop_after, timeout, seen, t0, last)
    finally:
        done.set()


def _drain(events, label, stop_after, timeout, seen, t0, last):
    for ev in events:
        last[0] = time.time()
        seen.append(ev)
        if ev.type in ("agent.tool_use", "agent.custom_tool_use"):
            zone = "local  " if ev.type == "agent.custom_tool_use" else "sandbox"
            print(f"    {DIM}{time.time()-t0:5.0f}s {zone} · {ev.name}{END}")
        elif ev.type == "session.status_idle":
            print(f"    {DIM}{time.time()-t0:5.0f}s idle · {ev.stop_reason.type}{END}")
        if stop_after and stop_after(ev):
            break
        if time.time() - t0 > timeout:
            raise Fail(f"{label}: no end of turn after {timeout}s")
    return seen


def verdict_for(sid):
    p = VERDICT_DIR / f"{sid}.json"
    return json.loads(p.read_text()) if p.exists() else None


# ── checkpoints ──────────────────────────────────────────────────────────────
def c0(A):
    # Catch a mangled key (placeholder left in, or another line glued onto it) before the API's bare 401.
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not re.fullmatch(r"sk-ant-[A-Za-z0-9_-]+", key):
        raise Fail("ANTHROPIC_API_KEY in .env is missing or malformed: it should be on its own line, "
                   "start with sk-ant-, and contain no spaces, quotes or '='")
    client.beta.agents.list(limit=1)
    ok(f"API key works with Managed Agents · your handle is '{state.handle()}'")


def c1(A):
    a, b = A.setup_environment(), A.setup_environment()
    need(a.startswith("env_"), f"environment ready: {a}")
    need(a == b, "calling it twice reuses the same environment (create once, use many)")
    cfg = client.beta.environments.retrieve(a).config
    need(getattr(cfg, "packages", None) and "pip-audit" in (cfg.packages.pip or []), "pip-audit is pre-installed via packages")


def c2(A):
    a, b = A.upload_vendor(), A.upload_vendor()
    need(a.startswith("file_"), f"vendor tarball ready: {a}")
    need(a == b, "re-running reuses the upload")


def c3(A):
    a, b = A.setup_agent(), A.setup_agent()
    need(a.startswith("agent_"), f"agent ready: {a}")
    need(a == b, "re-running reuses the agent")
    names = [getattr(t, "name", None) for t in client.beta.agents.retrieve(a).tools]
    need("record_verdict" in names, "agent has the custom record_verdict tool")


def c4(A):
    sid = A.start_vet(A.setup_agent(), A.setup_environment(), A.upload_vendor())
    try:
        s = client.beta.sessions.retrieve(sid)
        need(sid.startswith("sesn_"), f"session created: {sid}")
        need(s.metadata.get("owner") == state.handle(), "session metadata carries your owner handle")
        res = list(client.beta.sessions.resources.list(sid))
        need(any(getattr(r, "mount_path", "") and r.mount_path.endswith(".tar.gz") for r in res), "vendor tarball is mounted")
        need(s.budget is not None, "session has a budget cap")
        sid2 = A.start_vet(A.setup_agent(), A.setup_environment(), A.upload_vendor())
        if sid2 != sid:
            client.beta.sessions.delete(sid2)
        need(sid2 != sid, "a second call makes a new session (no state.sync here: every vet is fresh)")
    finally:
        client.beta.sessions.delete(sid)


def c5(A):
    sid = A.start_vet(A.setup_agent(), A.setup_environment(), A.upload_vendor())
    print(f"    {DIM}running a full vet in {sid} (≈1 min)…{END}")
    evs = drain(A.run_vet(sid, VET_PROMPT), "run_vet", quiet=180,
                stuck_hint="If the last line above is 'idle · requires_action', the session is waiting on "
                           "your app (see stub 5's questions).",
                stall_note="Stalled at requires_action: the session is waiting on your app. On the "
                           "half-written run_vet that's the stub 5 puzzle, not a bug. Not passed yet.")
    last = evs[-1] if evs else None
    if last is not None and last.type == "session.status_idle" and last.stop_reason.type == "requires_action":
        raise Fail("the session is idle with requires_action — it's waiting on your app (see the docstring)")
    need(any(e.type == "user.custom_tool_result" for e in evs) or verdict_for(sid), "you answered the custom tool call")
    v = verdict_for(sid)
    need(v is not None, f"verdict recorded locally: {v and v.get('verdict')} (risk {v and v.get('risk_score')})")
    need(last.type == "session.status_idle" and last.stop_reason.type == "end_turn", "turn ended with end_turn")


def c6_7(A):
    agent_id = A.setup_agent()
    sid = A.start_vet(agent_id, A.setup_environment(), A.upload_vendor())
    print(f"    {DIM}starting {sid}, then 'crashing' the app at the first sandbox tool call…{END}")
    gen = A.run_vet(sid, VET_PROMPT)
    drain(gen, "run_vet", stop_after=lambda e: e.type == "agent.tool_use")
    gen.close()  # the app is gone; the session is not
    print(f"    {DIM}app is down. the session keeps working without us; waiting until it parks on record_verdict…{END}")
    t0 = time.time()
    while client.beta.sessions.retrieve(sid).status != "idle":
        if time.time() - t0 > 300:
            raise Fail("session never went idle (5 min) — try again; the room may be rate-limited")
        time.sleep(5)
    print(f"    {DIM}…parked after {time.time() - t0:.0f}s with nobody listening. now 'restarting' the app{END}")
    found = A.find_open_session(agent_id)
    need(found == sid, "find_open_session() found the orphaned session instead of creating a new one")
    need(verdict_for(sid) is None, "nobody has answered record_verdict yet (the session is waiting for you)")
    evs = drain(A.resume(sid), "resume", quiet=300,
                stuck_hint="Is resume() answering the pending record_verdict from the HISTORY? "
                           "The session is waiting on you, so the live stream stays silent.")
    ids = [e.id for e in evs]
    need(len(ids) == len(set(ids)), "no duplicate events after reattaching")
    need(any(e.type == "user.message" for e in evs), "history was replayed (the original prompt is in it)")
    need(verdict_for(sid) is not None, "the pending verdict (found in the HISTORY, not the live stream) was answered")
    need(evs[-1].type == "session.status_idle" and evs[-1].stop_reason.type == "end_turn", "turn ended with end_turn")
    print(f"    {DIM}now reloading the app on the finished session…{END}")
    again = drain(A.resume(sid), "resume on a finished session", quiet=30,
                  stuck_hint="The history already ends the turn, so the live stream will never send "
                             "anything. See stub 7's last question.")
    need(len(again) == len(evs), "resume() on a finished session replays the history and returns, without waiting")


def c8(A):
    env_id = A.setup_environment()
    A.lock_down(env_id)
    net = client.beta.environments.retrieve(env_id).config.networking
    need(net.type == "limited", "environment networking is 'limited'")
    need(bool(getattr(net, "allow_package_managers", False)), "package managers still allowed (pip install works)")
    need("example.com" not in (getattr(net, "allowed_hosts", None) or []), "the beacon host is not allow-listed")
    print(f"    {DIM}now vet again in the app: look for the 🛡 chip and read the new evidence.{END}")


def c9(A):
    agent_id, env_id = A.setup_agent(), A.setup_environment()
    before = client.beta.agents.retrieve(agent_id).version
    old = client.beta.sessions.create(agent=agent_id, environment_id=env_id, metadata=state.owner(), title="pinned v1")
    try:
        new_version = A.ship_v2(agent_id)
        need(new_version > before, f"agent updated: v{before} → v{new_version}")
        new = client.beta.sessions.create(agent=agent_id, environment_id=env_id, metadata=state.owner(), title="v2")
        try:
            need(client.beta.sessions.retrieve(old.id).agent.version == before, f"the session created before the update is still on v{before}")
            need(client.beta.sessions.retrieve(new.id).agent.version == new_version, f"a new session gets v{new_version}")
        finally:
            client.beta.sessions.delete(new.id)
    finally:
        client.beta.sessions.delete(old.id)


STEPS = {0: ("API key", c0), 1: ("Environment", c1), 2: ("Files", c2), 3: ("Agent", c3),
         4: ("Session", c4), 5: ("Events + custom tool  ★ work it out #1", c5),
         6: ("Find + reattach  ★ work it out #2", c6_7), 7: ("Find + reattach  ★ work it out #2", c6_7),
         8: ("STRETCH · lock down the network", c8), 9: ("STRETCH · ship v2, keep v1 pinned", c9)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", type=int)
    ap.add_argument("--solution", action="store_true")
    args = ap.parse_args()
    A = importlib.import_module("solutions.agent" if args.solution else "agent")
    order = [args.step] if args.step is not None else [0, 1, 2, 3, 4, 5, 6]
    for n in order:
        label, fn = STEPS[n]
        print(f"\n[{'6–7' if n in (6, 7) else n}] {label}")
        try:
            fn(A)
        except NotImplementedError as e:
            print(f"  {RED}✗ implement {e or 'this stub'}() in agent.py{END}")
            sys.exit(1)
        except Fail as e:
            print(f"  {RED}✗ {e}{END}")
            sys.exit(1)
        except Exception as e:
            print(f"  {RED}✗ {type(e).__name__}: {e}{END}")
            sys.exit(1)
    print(f"\n{GREEN}All checkpoints passed.{END}")


if __name__ == "__main__":
    main()
