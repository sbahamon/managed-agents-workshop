# AGENTS.md: repo guide (for Claude Code and other coding agents)

This repo is a **take-home curriculum sample** for a Technical Curriculum Developer role (the brief itself isn't included). It teaches **Claude Managed Agents at a 201 level** to engineers who know the Messages API and may have tried the Agent SDK. The cohort, the instructor and the shared-key logistics are hypothetical. The code, the API calls, the costs and the timings are real and were tested.

> **If you are helping a lab participant** (anyone working inside `lab/` on `agent.py`), follow `lab/AGENTS.md`. In short: guide, explain and debug, but **never write the stub bodies in `lab/agent.py`** and never reveal `lab/solutions/agent.py`.

## Repo map

```
README.md                  reviewer index + 5-minute review path
DESIGN_NOTE.md             judgment calls: model proposed → shipped → why
INSTRUCTOR_GUIDE.md        one-page hand-off for the instructor (prep, stuck points, fallbacks)
process/                   session logs and drafts from building this with Claude
session/
  slides.html              ~12 min concept deck (single file, offline; arrow keys, N = speaker notes)
  notebook/repo_health.ipynb  ~8 min live demo: "Repo health report" product backend
  notebook/recorded/       cached outputs so the notebook renders with no key
  likely-questions.md      Q&A bank (the instructor guide's appendix)
lab/                       60-min hands-on lab: vendor vetting
  README.md                the learner guide (start here for the lab)
  AGENTS.md                rules for assisting participants
  agent.py                 LEARNER STUBS (keep them as stubs)
  solutions/agent.py       reference solution
  provided.py              system prompt, tools, custom-tool handler, helpers
  server.py, static/       FastAPI + single-page SSE timeline UI
  check.py                 checkpoints 0-9 (--solution to test the reference)
  cleanup.py               deletes resources tagged with your handle
  vendor/acme-csvkit/      the mock "malicious" package (harmless beacon to example.com)
  fixtures/                recorded runs for replay mode / instructor fallback
```

**Instructor guide:** `INSTRUCTOR_GUIDE.md`, written after dogfood pass 1. If you change a stuck point, a fallback command or a cost or timing, update it too.

## Ground rules for changes

1. **Official docs are the only source.** Code and claims come from platform.claude.com/docs (Managed Agents) and the installed SDK's type signatures. Don't copy or adapt code from other workshop repos or quickstarts. Comparing against them *after* writing is fine.
2. **Verify, don't recall.** Managed Agents is in beta and changes quickly. Check the docs (append `.md` to a docs URL for clean markdown) or the SDK types under `.venv/lib/python*/site-packages/anthropic/types/beta/` before asserting a field or behaviour.
3. **Keep the lab small.** Learners write about 40 lines. Don't add stubs, dependencies or third-party APIs. The scenario must work with mock data.
4. **Keep stubs and solution in sync.** If you change a helper or constant in `provided.py`, update `agent.py`'s "What you're given" block and docstrings (stub 5 shows `answer_custom_tool`'s body) and `solutions/agent.py`. If you change what `check.py` checks or its step numbers, update the ✅ Check footers in `agent.py` and the README. Then rerun the checks.
5. **No "airtight."** Describe the sandbox as isolated, disposable and egress-controllable. Don't make security claims we can't back.

## How to run things

```bash
python -m venv .venv && .venv/bin/pip install -r lab/requirements.txt jupyter matplotlib pandas
cp lab/.env.example .env      # or put ANTHROPIC_API_KEY in lab/.env

cd lab
../.venv/bin/python check.py --solution                 # all core checkpoints vs the reference (~2 min, ~10¢)
../.venv/bin/python check.py --solution --step 9        # stretch checks
MA201_SOLUTION=1 ../.venv/bin/uvicorn server:app        # app against the reference
MA201_REPLAY=fixtures/events.jsonl ../.venv/bin/uvicorn server:app   # no key needed
../.venv/bin/python cleanup.py --dry-run                # what's tagged with your MA201_HANDLE

open ../session/slides.html                             # deck (offline)
../.venv/bin/jupyter lab ../session/notebook/repo_health.ipynb
```

Use a distinct `MA201_HANDLE` for test runs (e.g. `MA201_HANDLE=dev-yourname`) and run `cleanup.py` afterwards.

## Facts measured while building (2026-10-19, anthropic 1.15.0, claude-sonnet-5-5)

- **A full vet:** about 40–70 s and 3–5¢ list cost. `check.py --solution` (steps 0–6) takes about 2 min.
- **Package installs:**
  - `syft` fails as an apt package and times out (about 100 s) as a go package, so the lab uses `pip-audit` via environment `packages.pip`.
  - Under `networking: limited` with `allow_package_managers: true`, pip and pip-audit still work.
  - Non-allow-listed hosts fail DNS (`Could not resolve host`).
- **Crashes and reattaching:**
  - Killing the client mid-run doesn't stop the session. It finishes its sandbox work and then idles at `requires_action` on `record_verdict`.
  - Reattaching works by opening the stream, then `events.list`, then deduping, then answering `stop_reason.event_ids`.
