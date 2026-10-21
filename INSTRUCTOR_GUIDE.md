# Instructor guide: Managed Agents 201

**You're teaching** a 20-minute intro session (split between conceptual introduction with [`session/slides.html`](session/slides.html) and practical application with the [notebook](session/notebook/repo_health.ipynb)) and a 60-minute lab ([`lab/README.md`](lab/README.md)). Assume a room of engineers who know the Messages API, sharing **one API key**. The lab is written so learners can finish without you; your job is the room: logistics, unblocking, and the wrap-up discussion. FAQ: [`session/likely-questions.md`](session/likely-questions.md) (the appendix to this guide).

**What the room should leave knowing.** 
- Anthropic runs the loop, the sandbox and the conversation state. 
- The agent is a versioned resource on the server, not code in your process.
- A session outlives your app: it waits for you (★ #1) and survives your crash (★ #2). 
- Big four concepts of a Managed Agent: Environment, Agent, Session, and Event
- Tie every hint you give back to one of these four.

## T-48h: prep checklist

- [ ] **Get the cohort key** with Managed Agents access. Set up as in the [README's "Run it for real"](README.md#run-it-for-real-needs-a-key-with-managed-agents-access) (venv, `pip install -r lab/requirements.txt`, key and your own `MA201_HANDLE` in `lab/.env`).
- [ ] **Ask the org admin** about concurrent-session, rate limits, and spend limit for audience size. The lab costs about $0.30/ learner, more with stretches.
- [ ] **Run the reference:** `cd lab && ../.venv/bin/python check.py --solution` (≈2 min, ≈10¢). All checks ✓ means the key, the model and the sandbox work today.
- [ ] **Do the lab once yourself**. This will give you a feel for what participants will struggle with.
- [ ] **Rehearse the deck and demo** (arrow keys; `N` toggles speaker notes). Notes overlay the slide, so **extend the display, don't mirror it**. Run the notebook live once.
- [ ] **Send participants the setup if possible** the day before: Python 3.10+, clone the repo, Claude Code installed. Setup is budgeted at 8 minutes, and a room that arrives cold will eat into stubs 1–4.

## Where learners get stuck

| Where | What you'll see | Stress this |
|---|---|---|
| Setup | `401`, or *key missing* | "Open `lab/.env`. One `NAME=value` per line, no quotes, and the key isn't glued to the line above it." |
| Setup | Two people see each other's sessions | "Is your `MA201_HANDLE` unique?" Collect handles at the start (you'll need them for cleanup). In the Console, environments and agents are named `vendor-vetting-<handle>` / `vendor-vetter-<handle>`; `metadata.owner` carries the handle too. |
| Setup | `command not found: python` in a `!` command | "Use `.venv/bin/python`." Claude Code's `!` shell may not have the venv active; every ✅ Check already says `.venv/bin/python`. |
| Stubs 1–4 | SDK argument errors: `environment=` vs `environment_id=`, `env_id=`, positional args to `sessions.list` | "The resource id goes first and positional; everything else is keyword. Don't get stuck on Python syntax. Ask Claude Code to read the signature." |
| Stubs 1–4 | Overrun: estimated 12–18 min vs 12 slotted (run 2: about 21 min, about 5 of them on the `python` path, since fixed) | At minute 22, tell anyone not on stub 5 to copy stubs 1–4 from `solutions/agent.py`. The ★ steps are the lesson; these aren't. |
| ★ Stub 5 | Amber `requires_action` banner, nothing happens | Don't explain it. Ask: "Idle isn't done. Who is the session waiting on? Which event names the call?" The two-line fix is the easy part; the diagnosis is the lesson. |
| ★ Stub 5 | Learner writes their own `events.send` alongside `answer_custom_tool` | "Read what the stub 5 docstring says the helper sends." |
| ★ Stub 7 | Duplicate boxes after reattach, or reattach hangs | Duplicates: "Which did you open first, the stream or the history list?" Hang: "Was the turn already over before you started listening?" |
| ★ Stub 7 | `check.py --step 7` looks frozen | A 1–2 min quiet wait is normal: it crashes a vet on purpose and waits for it to park. Past ~4 min, `resume()` isn't answering the pending `record_verdict`. |
| Stubs 6–9 | `.order()` on a page, `.version()` | "List calls return pages; iterate or wrap in `list(...)`. `version` is an attribute." |

**Claude Code** is told (by `lab/AGENTS.md`) to coach rather than write the stubs. In dogfooding it held to that but slipped three times; if a learner says "Claude told me…", check it against the docstring, and push back on Claude Code by asking it to verify.

## Fallbacks when things break

| Problem | Do this |
|---|---|
| **API down, or the key doesn't work on the day** | Session: the notebook switches to replay with no key (`REPLAY=1` forces it) and renders the same charts from `recorded/`. Lab: `MA201_REPLAY=fixtures/events.jsonl uvicorn server:app` drives the full UI; `fixtures/killed-mid-run.jsonl` shows the reattach. Walk the room through the stubs against the replay and the solution. |
| **Rate-limited** (turns take >4 min, 429s) | Pair learners up on one machine, which halves the load. Have the rest watch the replay until it clears. |
| **One learner badly behind** | Copy stubs 1–4 from the solution, and protect their time for ★ #1. Skip ★ #2 if needed; it's tested on its own. |
| **A session runs away** | Each session is capped at 75¢ (`MA201_BUDGET_CENTS`). `budget_reached` idles the session; it doesn't keep spending. |
| **Live demo fails mid-session** | Set `REPLAY=1` and rerun the notebook cell. Say so: "recorded earlier today, same code." |

**After class:** remind everyone to run `python cleanup.py` (it only touches their handle). For anyone who left without doing it, run `MA201_HANDLE=<their-handle> python cleanup.py` yourself, using the handles you collected. Idle sessions don't bill, so there's no rush.
