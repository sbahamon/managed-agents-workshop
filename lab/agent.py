"""YOUR CODE GOES HERE. Fill in each stub in order; the web app lights up as you go.

Each stub is one Managed Agents concept. Hints point at the official docs —
read the linked section, then write the call.

HOW THIS LAB WORKS: three windows, one job each
  ┌──────────────┬──────────────────────────────────────────────────────────────┐
  │ agent.py     │ You write the stubs here. Each one shows the call's shape,   │
  │ (this file)  │ links the docs, and ends with a ✅ Check.                    │
  ├──────────────┼──────────────────────────────────────────────────────────────┤
  │ Claude Code  │ Your copilot: explains, points at docs, debugs (but won't    │
  │              │ write the stubs). Ask it to start the app server; it runs it │
  │              │ in the background and reads its log. Run checks here with    │
  │              │ `!`, e.g.  ! .venv/bin/python check.py --step 1              │
  ├──────────────┼──────────────────────────────────────────────────────────────┤
  │ The app      │ http://localhost:8000. Each stub lights up as it passes;     │
  │ (browser)    │ from stub 5 the session's events stream into the timeline.   │
  └──────────────┴──────────────────────────────────────────────────────────────┘

WHAT YOU'RE GIVEN (already imported below; you never need to open provided.py)
  client          an anthropic.Anthropic() client. Managed Agents calls live under client.beta.*
  MODEL           the model id, e.g. "claude-sonnet-5-5"
  SYSTEM          the reviewer's system prompt (a few paragraphs of plain text)
  TOOLS           [{"type": "agent_toolset_20260401"}, RECORD_VERDICT]
                    = the built-in sandbox tools (bash, files, …) + our ONE custom tool
  ENV_PACKAGES    {"type": "packages", "pip": ["pip-audit"]}   pass it as-is
  MOUNT_PATH      where the vendor tarball appears inside the sandbox
  BUDGET_CENTS    the per-session spending cap, as a string of cents (default "75")
  vendor_tarball()                    the vendor package as .tar.gz bytes
  answer_custom_tool(session_id, event)  run record_verdict locally + send the result (see stub 5)
  turn_over(event)                    True when the agent's turn is really finished (end_turn,
                                      terminated, …). NOT on requires_action: that's a pause
                                      waiting on you, so the stream stays open but goes quiet.
  needs_attention(session)            True if a session is still running, or paused waiting on you
  pending_custom_tool_calls(history)  the custom tool calls in a history list still awaiting a result
  state.sync(key, fn)  run fn() once, remember its result in .ma201-state.json, reuse it after
  state.handle()       your MA201_HANDLE           state.owner()  metadata to tag what you create

SDK call shapes: the resource id (env, agent, session) goes first and positional;
everything else is a keyword argument. list(...) calls return a PAGE, not a list:
loop over it (the next page is fetched only when your loop gets there, so returning
early stops early), or wrap it in list(...) to fetch every page at once. .data is only
the first page (the docs' samples use .data, so watch for that).
"""
from __future__ import annotations

from typing import Iterator, Optional

import state
from provided import (
    BUDGET_CENTS, ENV_PACKAGES, MODEL, MOUNT_PATH, SYSTEM, TOOLS,
    answer_custom_tool, client, needs_attention, pending_custom_tool_calls,
    turn_over, vendor_tarball,
)


# ─────────────────────────────────────────────────────────────────────────────
# 0 ── SETUP: do this before stub 1
# ─────────────────────────────────────────────────────────────────────────────
#   1. Start Claude Code from lab/ (VS Code's terminal, or any terminal).
#   2. In Claude Code, check your key:   ! .venv/bin/python check.py --step 0
#      (Windows: ! .venv\Scripts\python check.py --step 0). It prints your handle.
#   3. Ask Claude Code: "Start the app and explain what I'm looking at."
#      Then open http://localhost:8000. You'll see 7 grey stubs.
#
#   Every ✅ Check below runs the same way, with .venv/bin/python (not plain
#   python: Claude Code's ! shell may not have your venv active). The long ones
#   (stubs 5–7) take minutes, so ask Claude Code to run those in the background.


# ─────────────────────────────────────────────────────────────────────────────
# 1 ── ENVIRONMENT: the sandbox template every session is built from
# ─────────────────────────────────────────────────────────────────────────────
def setup_environment() -> str:
    """Create a cloud environment ONCE and return its id.

    The shape (fill in the ...; the docs tell you the values):

        return state.sync("environment_id", lambda: client.beta.environments.create(
            name=f"vendor-vetting-{state.handle()}",   # unique: on a shared key, names tell them apart
            config={
                "type": ...,             # a cloud environment
                "networking": {"type": ...},   # an object, not a string: unrestricted, for now
                                               # (stretch 8 locks it down)
                "packages": ENV_PACKAGES,
            },
            metadata=state.owner(),      # lets cleanup.py find it on a shared key
        ).id)

    state.sync runs the lambda once and remembers the id, so re-running reuses
    the same environment instead of making a new one. Note the .id at the end.

    Docs: https://platform.claude.com/docs/en/managed-agents/environments#create-an-environment
          https://platform.claude.com/docs/en/managed-agents/environments#packages

    ✅ Check:  ! .venv/bin/python check.py --step 1          (a few seconds)
       Passes when: an env_… id prints, a second call reuses it, pip-audit is pre-installed.
       In the app:  stub 1 turns green and environment_id appears under the rail.
    """
    raise NotImplementedError("setup_environment")


# ─────────────────────────────────────────────────────────────────────────────
# 2 ── FILES: get the untrusted vendor code into Anthropic's storage
# ─────────────────────────────────────────────────────────────────────────────
def upload_vendor() -> str:
    """Upload the vendor tarball ONCE (state key "file_id") and return the file id.

    Same pattern as stub 1: state.sync(<key>, lambda: <create call>.id).
    The upload call takes one keyword argument, file=, whose value is a
    (filename, bytes, mime_type) tuple:

        client.beta.files.upload(file=("acme-csvkit.tar.gz", vendor_tarball(), "application/gzip"))

    Docs: https://platform.claude.com/docs/en/managed-agents/files#uploading-files

    ✅ Check:  ! .venv/bin/python check.py --step 2          (a few seconds)
       Passes when: a file_… id prints and a second call reuses it.
       In the app:  stub 2 turns green and file_id appears under the rail.
    """
    raise NotImplementedError("upload_vendor")


# ─────────────────────────────────────────────────────────────────────────────
# 3 ── AGENT: a versioned, server-side definition (model + prompt + tools)
# ─────────────────────────────────────────────────────────────────────────────
def setup_agent() -> str:
    """Create the agent ONCE (state key "agent_id") and return its id.

    Same pattern again. The create call takes these keyword arguments:

        client.beta.agents.create(name=..., model=..., system=..., tools=..., metadata=...)

    Use MODEL, SYSTEM and TOOLS, a unique name like f"vendor-vetter-{state.handle()}",
    and metadata=state.owner().

    TOOLS is [{"type": "agent_toolset_20260401"}, RECORD_VERDICT]. The first entry
    turns on the built-in tools (bash, file reads and edits, …), which run in
    Anthropic's sandbox. The second is our custom tool, record_verdict, which the
    agent calls but YOUR process runs (stub 5).

    Notice what you are NOT writing: no agent loop, no tool executor for bash.

    Docs: https://platform.claude.com/docs/en/managed-agents/agent-setup#create-an-agent
          https://platform.claude.com/docs/en/managed-agents/tools#custom-tools

    ✅ Check:  ! .venv/bin/python check.py --step 3          (a few seconds)
       Passes when: an agent_… id prints, a second call reuses it, and the agent has record_verdict.
       In the app:  stub 3 turns green and agent_id appears under the rail.
    """
    raise NotImplementedError("setup_agent")


# ─────────────────────────────────────────────────────────────────────────────
# 4 ── SESSION: one running instance = one fresh sandbox
# ─────────────────────────────────────────────────────────────────────────────
def start_vet(agent_id: str, env_id: str, file_id: str) -> str:
    """Create a NEW session on every call and return its id.

    ⚠ No state.sync this time. Stubs 1–3 made things you build once and reuse:
    a template, a file, a definition. A session is one vet (one order, cooked at
    its own station), so every call makes a fresh one. If you cache it, every vet
    goes back to the same old session.

        client.beta.sessions.create(agent=..., environment_id=..., resources=..., ...)

    Note the names: the agent goes in agent= (no _id), the environment in environment_id=.

    - mount the uploaded file:  resources=[{"type": "file", "file_id": ..., "mount_path": MOUNT_PATH}]
    - metadata:  {**state.owner(), "target": "acme-csvkit"}   ← stub 6 will rely on this
    - budget:    {"type": "limit", "max_list_cost": {"amount": BUDGET_CENTS, "currency": "USD"}}
    - title:     anything human-readable

    Docs: https://platform.claude.com/docs/en/managed-agents/sessions#creating-a-session
          https://platform.claude.com/docs/en/managed-agents/files#mounting-files-in-a-session
          https://platform.claude.com/docs/en/managed-agents/sessions#set-a-session-budget

    ✅ Check:  ! .venv/bin/python check.py --step 4          (a few seconds)
       Passes when: a sesn_… id prints, with your owner metadata, the tarball mounted, and a budget,
                    and a second call makes a different session.
       In the app:  stub 4 turns green. Clicking Vet now starts a session (stub 5 is next).
    """
    raise NotImplementedError("start_vet")


# ─────────────────────────────────────────────────────────────────────────────
# 5 ── EVENTS  ★ WORK IT OUT #1 ★
# ─────────────────────────────────────────────────────────────────────────────
def run_vet(session_id: str, prompt: str) -> Iterator:
    """Send the prompt and yield every event the session streams back.

    This one is half-written for you. Run it as-is first (click "Vet" in the
    app) and watch what happens near the end of the run.

    Questions to answer before you change anything:
      • The session goes idle — but with which stop_reason? (look at the badge)
      • Who is supposed to run record_verdict: Anthropic's sandbox, or you?
      • What event does the session need from you before it can continue?

    You don't build that event yourself. answer_custom_tool(session_id, event)
    does the "you run it" half. Pass it the whole agent.custom_tool_use event,
    not event.id (it reads the tool's name and input from it). It returns
    nothing. Inside, it does:

        text = <run record_verdict locally with event.input>   # saves .verdicts/<session>.json
        client.beta.sessions.events.send(session_id, events=[{
            "type": "user.custom_tool_result",
            "custom_tool_use_id": event.id,     # ← links the reply to the paused call
            "content": [{"type": "text", "text": text}],
        }])

    (The docs also mention user.tool_confirmation. That's the reply when a
    permission policy asks you to approve a tool call; this lab has none.)

    Your job: work out WHEN to call it. Keep the turn_over check: it ends the
    loop on every kind of finish, not just end_turn.

    Docs: https://platform.claude.com/docs/en/managed-agents/events-and-streaming#answer-tool-calls-that-pause-the-session
          https://platform.claude.com/docs/en/managed-agents/events-and-streaming#respond-when-the-session-goes-idle

    ✅ Check:  ! .venv/bin/python check.py --step 5   (one full vet: about 1 min, about 5¢)
       If it moves to the background after 120 s, ask Claude Code for its output.
       Passes when: you answered the custom tool call, a verdict is saved locally,
                    and the turn ends with end_turn (not requires_action).
       In the app:  click Vet. The timeline ends on idle · end_turn and the
                    Verdict panel shows BLOCK.
       On the half-written version, the check stalls at "idle · requires_action",
       prints a hint after 90 s and gives up at 3 min with a ⏸ "stalled" line (not a
       red ✗). That's the puzzle, not a bug.
    """
    # Open the stream BEFORE sending, so no early events are missed.
    with client.beta.sessions.events.stream(session_id) as stream:
        client.beta.sessions.events.send(session_id, events=[
            {"type": "user.message", "content": [{"type": "text", "text": prompt}]},
        ])
        for event in stream:
            yield event

            if turn_over(event):
                return


# ─────────────────────────────────────────────────────────────────────────────
# 6 ── FIND, DON'T CREATE
# ─────────────────────────────────────────────────────────────────────────────
def find_open_session(agent_id: str) -> Optional[str]:
    """Return the id of YOUR most recent session that still needs attention, or None.

    The server calls this when the app starts. If your app crashed mid-vet, the
    session didn't — it's still in Anthropic's cloud, maybe still working, maybe
    paused waiting on you.

        client.beta.sessions.list(agent_id=..., order=..., limit=...)   # keyword arguments only

    - List this agent's sessions, newest first.
    - It returns a page: loop over it. Filtering and sorting
      are arguments to list(), not methods on the result.
    - Keep only the ones whose s.metadata.get("owner") is state.handle()
      (everyone in the room may share one API key!). metadata is a dict
      attribute on the session; the session itself has no .get.
    - needs_attention(session) tells you if it's still running or paused on
      requires_action.
    - Return the match's id (s.id, a str), not the session object.

    Docs: https://platform.claude.com/docs/en/api/python/beta/sessions/list

    ✅ Check:  stub 6 is tested together with stub 7, so write both, then check
       --step 7 (see stub 7's ✅ Check).
    """
    raise NotImplementedError("find_open_session")


# ─────────────────────────────────────────────────────────────────────────────
# 7 ── REATTACH  ★ WORK IT OUT #2 ★
# ─────────────────────────────────────────────────────────────────────────────
def resume(session_id: str) -> Iterator:
    """Pick an existing session back up: rebuild the timeline, rescue anything
    the session is waiting on, and keep following it live.

    You have two ways to read a session's events:
      (a) client.beta.sessions.events.stream(session_id)  — live only, from the moment it opens
      (b) client.beta.sessions.events.list(session_id, order="asc")  — everything so far
          (a page: wrap it in list(...) to get every event as a real list you can search
          and reverse. The docs' sample loops over .data, which is only the first page.)

    Before you write anything, answer these (out loud, or with a neighbour):
      • You need both (a) and (b). If an event happens BETWEEN your two calls,
        which order loses it? Which order shows it to you twice?
      • If you see an event twice, what will the UI do? What's unique per event?
      • The app died while the agent was calling record_verdict. Where is that
        call now, and how do you know it's still unanswered?
        (pending_custom_tool_calls(history) does the lookup: pass it the history
        list, and it returns the agent.custom_tool_use events still waiting.)
      • If the history shows the turn already ended, should you open-and-wait at all?

    Then write it. Reuse what you learned in stub 5 for anything that arrives live.
    The docs' reconnect section is the recipe for the first two questions; the
    last two are specific to this app.

    Docs: https://platform.claude.com/docs/en/managed-agents/events-and-streaming#reconnect-without-missing-events
          https://platform.claude.com/docs/en/managed-agents/events-and-streaming#list-past-events
          https://platform.claude.com/docs/en/managed-agents/events-and-streaming#respond-when-the-session-goes-idle

    ✅ Check:  ask Claude Code: "run check.py --step 7 in the background"
               (covers stubs 6 and 7: about 2–4 min, about 5¢. Too long for !, which
               moves to the background after 120 s.)
       It starts a vet, "crashes" your app, waits for the session to park on
       record_verdict with nobody listening, then calls your find + resume.
       The long quiet wait in the middle is expected.
       Passes when: find_open_session finds the orphan, the history is replayed with
                    no duplicates, the pending verdict is answered, and the turn ends.
                    Then it calls resume() again on the finished session, which must
                    return within 30 s instead of waiting on a silent stream.
       In the app:  kill the server mid-vet, restart it, reload. The same session id
                    comes back with a ↻ replayed tag and finishes.
    """
    raise NotImplementedError("resume")


# ═════════════════════════════════════════════════════════════════════════════
# STRETCH GOALS
# ═════════════════════════════════════════════════════════════════════════════

# 8 ── ENVIRONMENT: lock down the sandbox's network
def lock_down(env_id: str) -> None:
    """Change the environment so sandbox code can reach package registries but
    nothing else. Then vet again: what happens to the beacon, and does the
    agent's verdict change?

        client.beta.environments.update(env_id, config={...})   # env id positional, config keyword

    config must still say "type": "cloud" (it tells the API which kind of config
    this is). Other fields you omit, like packages, keep their current value.
    Networking type "limited"; think about allowed_hosts and allow_package_managers
    (we still pip install!). Start a NEW vet to see the change.

    Docs: https://platform.claude.com/docs/en/managed-agents/environments#networking
          https://platform.claude.com/docs/en/api/python/beta/environments/update

    ✅ Check:  ! .venv/bin/python check.py --step 8          (a few seconds)
       Passes when: networking is limited, package managers are still allowed,
                    and example.com isn't allow-listed.
       In the app:  vet again. The beacon probe fails with "Could not resolve host"
                    and a 🛡 chip appears. The verdict should still be BLOCK.
       The linked docs describe a blocked host as an HTTP 403 that names the host.
       In this lab you'll see "Could not resolve host" instead: the sandbox's DNS
       lookup for example.com fails before any request is made. Same lockdown,
       earlier failure.
    """
    raise NotImplementedError("lock_down")


# 9 ── AGENT: ship v2 without breaking v1
def ship_v2(agent_id: str) -> int:
    """Update the agent (e.g. append a stricter policy to SYSTEM) and return the
    new version number. That's all this function does: you don't create any
    sessions here.

        current = client.beta.agents.retrieve(agent_id)       # current.version is an int attribute
        client.beta.agents.update(agent_id, version=..., system=...)   # returns the updated agent

    `version` on update is optional; passing the version you read makes the
    update fail (409) if someone else changed the agent first. Use it.

    Docs: https://platform.claude.com/docs/en/managed-agents/agent-setup#update-an-agent
          https://platform.claude.com/docs/en/managed-agents/agent-setup#list-versions

    ✅ Check:  ! .venv/bin/python check.py --step 9          (a few seconds)
       The check starts one session before calling your function and one after,
       then reads sessions.retrieve(...).agent.version on each.
       Passes when: the agent goes v1 → v2, the earlier session is still on v1,
                    and the new one gets v2.
       It passes once per agent. Rerun it with the same system prompt and you'll see
       "✗ agent updated: v2 → v2": an update that changes nothing makes no new version.
       To run it again, change the policy text (or run cleanup.py and start fresh).
    """
    raise NotImplementedError("ship_v2")


# ═════════════════════════════════════════════════════════════════════════════
# DONE? Tidy up everything tagged with your handle:
#     ! .venv/bin/python cleanup.py --dry-run      # see what would be removed
#     ! .venv/bin/python cleanup.py                # remove it
# ═════════════════════════════════════════════════════════════════════════════
