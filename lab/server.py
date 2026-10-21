"""Provided: the lab web app. You do NOT need to edit this file.

    uvicorn server:app --reload            # uses your stubs in agent.py
    MA201_SOLUTION=1 uvicorn server:app    # uses solutions/agent.py
    MA201_REPLAY=fixtures/events.jsonl uvicorn server:app   # no API key needed

The server calls the functions you write in agent.py, pushes every session
event into an in-memory buffer, and streams that buffer to the browser over
Server-Sent Events. The browser folds events into the timeline you see.
"""
from __future__ import annotations

import asyncio
import importlib
import inspect
import json
import os
import threading
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

import state

HERE = Path(__file__).resolve().parent
REPLAY = os.environ.get("MA201_REPLAY")
RUNS = HERE / ".runs"

if REPLAY:
    agent = None
else:
    agent = importlib.import_module("solutions.agent" if os.environ.get("MA201_SOLUTION") else "agent")
    import provided

app = FastAPI(title="MA201 vendor vetting lab")

BUFFERS: dict[str, list[dict]] = {}
DONE: set[str] = set()
LAST: list[str] = []  # most recent session this process followed (so a reload can show it)

STUBS = [
    (1, "setup_environment", "Environment"),
    (2, "upload_vendor", "Files"),
    (3, "setup_agent", "Agent"),
    (4, "start_vet", "Session"),
    (5, "run_vet", "Events + custom tool"),
    (6, "find_open_session", "Find, don't create"),
    (7, "resume", "Reattach"),
]


def _implemented(name: str) -> bool:
    if agent is None:
        return True
    try:
        src = inspect.getsource(getattr(agent, name))
    except (AttributeError, OSError):
        return False
    return "NotImplementedError" not in src


def _stub_status() -> list[dict]:
    out = []
    for n, name, label in STUBS:
        done = _implemented(name)
        if n == 5 and agent is not None:
            # run_vet starts out half-written; it's "done" once a verdict has come back.
            done = done and any((HERE / ".verdicts").glob("*.json"))
        out.append({"n": n, "name": name, "label": label, "done": done})
    return out


def _lab_error(sid: str, exc: BaseException) -> None:
    if isinstance(exc, NotImplementedError):
        msg = f"Not implemented yet: {exc}" if str(exc) else "A stub in agent.py isn't implemented yet."
    else:
        msg = f"{type(exc).__name__}: {exc}"
    BUFFERS[sid].append({"id": f"lab-{time.time()}", "type": "lab.error", "message": msg})


def _pump(sid: str, events) -> None:
    """Drain an iterator of SDK events into the session's buffer (in a thread)."""
    RUNS.mkdir(exist_ok=True)
    log = (RUNS / f"{sid}.jsonl").open("a")
    try:
        for ev in events:
            d = ev if isinstance(ev, dict) else ev.model_dump(mode="json")
            BUFFERS[sid].append(d)
            log.write(json.dumps(d) + "\n")
            log.flush()
    except BaseException as exc:  # surface everything in the UI
        _lab_error(sid, exc)
    finally:
        log.close()
        DONE.add(sid)


def _start(sid: str, events, *, reattached: bool = False) -> None:
    BUFFERS[sid] = [{"id": "lab-replayed", "type": "lab.replayed"}] if reattached else []
    DONE.discard(sid)
    LAST[:] = [sid]
    threading.Thread(target=_pump, args=(sid, events), daemon=True).start()


def _ids() -> dict:
    return {k: state.get(k) for k in ("environment_id", "file_id", "agent_id")}


# ── Routes ───────────────────────────────────────────────────────────────────
@app.get("/")
def index():
    return FileResponse(HERE / "static" / "index.html")


@app.get("/api/status")
def status():
    return {
        "handle": state.handle(),
        "mode": "replay" if REPLAY else ("solution" if os.environ.get("MA201_SOLUTION") else "stubs"),
        "model": None if REPLAY else provided.MODEL,
        "stubs": _stub_status(),
        "ids": _ids(),
    }


@app.post("/api/setup")
def setup():
    if REPLAY:
        return {"ids": {"environment_id": "env_replay", "file_id": "file_replay", "agent_id": "agent_replay"}}
    steps = [("environment_id", agent.setup_environment), ("file_id", agent.upload_vendor),
             ("agent_id", agent.setup_agent)]
    ids = {}
    for key, fn in steps:
        try:
            ids[key] = fn()
        except NotImplementedError:
            return JSONResponse({"ids": ids, "error": f"Implement {fn.__name__}() in agent.py"}, 400)
        except Exception as exc:
            return JSONResponse({"ids": ids, "error": f"{fn.__name__}: {type(exc).__name__}: {exc}"}, 400)
    return {"ids": ids}


@app.post("/api/vet")
def vet():
    if REPLAY:
        sid = "sesn_replay"
        _start(sid, _replay_events())
        return {"session_id": sid}
    ids = setup()
    if isinstance(ids, JSONResponse):
        return ids
    ids = ids["ids"]
    try:
        sid = agent.start_vet(ids["agent_id"], ids["environment_id"], ids["file_id"])
    except NotImplementedError:
        return JSONResponse({"error": "Implement start_vet() in agent.py"}, 400)
    except Exception as exc:
        return JSONResponse({"error": f"start_vet: {type(exc).__name__}: {exc}"}, 400)
    _start(sid, agent.run_vet(sid, provided.VET_PROMPT))
    return {"session_id": sid}


@app.post("/api/reattach")
def reattach():
    """Called by the page on load: is there a session of ours we should show or pick back up?"""
    if REPLAY:
        return {"session_id": None}
    active = [sid for sid in BUFFERS if sid not in DONE]
    if active:  # already following one in this process
        return {"session_id": active[-1], "already": True}
    agent_id = state.get("agent_id")
    sid = None
    if agent_id:
        try:
            sid = agent.find_open_session(agent_id)
        except NotImplementedError:
            pass
    if sid:
        _start(sid, agent.resume(sid), reattached=True)
        return {"session_id": sid, "reattached": True}
    if LAST:  # nothing open: re-show the last session this process followed
        return {"session_id": LAST[0], "already": True}
    return {"session_id": None}


@app.get("/api/sessions/{sid}/events")
async def events(sid: str):
    if sid not in BUFFERS:
        raise HTTPException(404, "unknown session (restart? try reattach)")

    async def gen():
        i = 0
        while True:
            buf = BUFFERS.get(sid, [])
            while i < len(buf):
                yield f"data: {json.dumps(buf[i])}\n\n"
                i += 1
            if sid in DONE and i >= len(BUFFERS.get(sid, [])):
                yield "event: done\ndata: {}\n\n"
                return
            await asyncio.sleep(0.25)

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/api/sessions/{sid}/verdict")
def verdict(sid: str):
    path = HERE / ".verdicts" / f"{sid}.json"
    if not path.exists():
        raise HTTPException(404, "no verdict recorded")
    return json.loads(path.read_text())


# ── Replay mode ──────────────────────────────────────────────────────────────
def _replay_events():
    """Re-emit a recorded run with compressed timing (no API calls)."""
    path = HERE / REPLAY if not Path(REPLAY).is_absolute() else Path(REPLAY)
    for line in path.read_text().splitlines():
        if line.strip():
            ev = json.loads(line)
            time.sleep(0.6 if ev.get("type", "").startswith("agent.") else 0.15)
            yield ev
