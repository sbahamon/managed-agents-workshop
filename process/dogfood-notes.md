# Dogfood notes

> **When you finish:** export the Claude Code session (`/export`) and save it in `process/session-logs/`.

## Session (slides + notebook)

- **Design critique (subagent, frontend-design skill), applied on `dogfood-pass-1`:**
  - Cut to 8 slides: removed the loop slide (assumed knowledge at 201) and "Where the metaphor breaks" (its cards repeated later slides; notes moved, not deleted).
  - Merged "Anatomy of one turn" and "Two zones" into one swim-lane slide (your process / session / sandbox × time), built in 4 clicks. Custom tool calls come from the **session**, not the sandbox; the sandbox lane just says "built-in toolset".
  - "Objects" → "concepts" everywhere, matching the docs' overview.
  - One meaning per colour; contrast ≥4.5:1; embedded Kalam font so projector PCs don't fall back to Comic Sans.
- **Still open:**
  - Slide 8's lab thumbnail ("See it, then build it") is unreadable at that size. Replace it with a cropped detail (one sandbox card, one local card, the BLOCK verdict). Needs a fresh app screenshot.
  - Speaker notes (N) overlay the slide, so a mirrored projector shows them to the room. Add "extend the display, don't mirror" to the instructor guide, or build a presenter window.
  - ~~Not yet rehearsed against the 12-minute budget with the new timings.~~ Done in run 2, below.
- **Run 2 (2026-10-20), deck + notebook out loud: 18 min against a 20-min budget.**
  - Slides: 10 min (budget 12). Notebook: 8 min (budget 8).
  - Notebook live: session A took about 27 s (run 1: 18 s); downloading the output files took under 3 s. Variance, not a regression, but tell the instructor to expect 20–30 s.
  - Slide 4 metaphor: a ticket and a meal are the same level, but an event is *part of* a session. Changed events from "the ticket rail" to **the call-outs**: each step of cooking the order, called out as it happens, both ways (order in, "stop!"), and logged. Session is now "cooking one order". Kept the restaurant (considered a chef/workday/meal version, the sorcerer's broom and car models; "model" clashes with the Claude model).

## Lab

| Step | Minutes | Notes / where I got stuck |
|---|---|---|
| Setup (0) | | `.env` 401: root `.env` had no trailing newline, so an appended key merged into the previous line (fixed on main in `082ed3c`). |
| Stubs 1–4 | | Python syntax more than concepts: assignment inside a lambda, missing `.id`, `ENV_PACKAGES` used as a string then a dict key, the `(filename, bytes, mime_type)` tuple read as literal code, `environment=` vs `environment_id=`. |
| ★ #1 `run_vet` | | Unsure whether to send `user.custom_tool_result` or `user.tool_confirmation`; duplicated `answer_custom_tool`'s send; replaced `turn_over` with an `end_turn`-only break (hangs on other endings). |
| ★ #2 `resume` | | Hard. Chained `.order()` on a page, used `&&`, yielded before the dedupe check, ran `pending_custom_tool_calls` inside the live loop, didn't wrap `events.list` in `list(...)`. `--step 6` hung past Claude Code's 120 s `!` timeout. |
| Stretch 8 / 9 | | Stub 8: `env_id=` keyword, then omitted `"type": "cloud"`. Stub 9: created sessions inside `ship_v2`, used `versions.list`, wrote `.version()` / `.versions()`. |

*Minutes not recorded this run. Full log: `process/session-logs/trial-run-transcript.txt`.*

### Run 2 (2026-10-20, 8:36–9:53 PM; on a call, with one internet drop)

| Step | Minutes (budget) | Notes / where I got stuck |
|---|---|---|
| Stubs 1–4 | about 21 (12) | About 5 min on the shell: `command not found: python` (no venv in `!`'s shell), `--step1`, `check.py` with no `python`. Stub 1: `"networking": "unrestricted"` as a string (400). Stub 4: not obvious it skips `state.sync`, and step 4 didn't catch caching. |
| ★ #1 `run_vet` | about 14 (12) | Right moment, wrong argument: `answer_custom_tool(..., event=event.id)`. |
| ★ #2 `resume` | about 42 (15) | About 10 min lost to the internet drop and the 120 s `!` timeout. Stub 6: returned the session, not its id; `metadata["owner"]` then `session.get(...)`. Stub 7 passed with two gaps the check didn't test: stream events not deduped, and a hang when the turn had already ended. Claude Code wrongly said `limit` caps a `list(...)`, then corrected itself. |

Fixes on `lab-fixes-run2` (`whats-left.md` 2b): step 0 block, `.venv/bin/python` everywhere, long checks via Claude Code, the docstring slips above, `check.py` catching the cached session and the ended-turn hang, `✗ expected:` wording. **Not fixed:** stubs 6–7 still run about 2× their slot. Full log: `process/session-logs/dogfood-2.txt`.

## Claude Code as a guide (lab/AGENTS.md)

Mostly good: it kept to hints and questions on the ★ stubs and didn't write stub bodies. Slips worth fixing in `lab/AGENTS.md` or the docstrings:

- **Unchecked shell advice.** It suggested `echo ... >> ../.env` without checking the file ended in a newline, which produced the setup 401.
- **Wrong API claim on stub 8.** It said `config` didn't need `"type"` on update. It does (the docstring misled it the same way it misleads learners).
- **Premature "done".** On stub 7 it said a fix (`list(...)`) was in place when it wasn't, then corrected itself.
- **Pointed at `provided.py` twice** (see the `provided.py` finding below).
- **Positive:** reading the SDK signature to explain keyword-only vs positional arguments was the most useful kind of help. Encourage it in `lab/AGENTS.md`.

## Changes to make

> **Dogfooding findings. Not applied yet.** Captured while working through the lab as a learner. They feed a follow-up revision pass rather than being changed mid-run.

- **Stub 1 docstring is too terse; I fumbled writing the environment.** The bullet list (`name` / `config` / `metadata`) doesn't show the shape of the call. Mistakes I made:
  - I wrapped `ENV_PACKAGES` in another dict (`{"type": ENV_PACKAGES, "pip": [...]}`) without realising it's already the full packages object.
  - I forgot `.id` inside the `state.sync` lambda.

  Fix: add a skeleton to the docstring with the plumbing visible and the concept values blanked:

  ```python
  return state.sync("environment_id", lambda: client.beta.environments.create(
      name=...,
      config={
          "type": ...,
          "networking": {...},
          "packages": ENV_PACKAGES,
      },
      metadata=...,
  ).id)
  ```

  - **Keep visible:** `state.sync` + lambda, the `config` nesting, `.id`. That's lab plumbing, not a Managed Agents concept.
  - **Show `ENV_PACKAGES` filled in.** It's a provided constant, and blanking it is how I double-wrapped it.
  - **Blank:** the `type` and `networking` values. The docs link answers them, and it sets up stretch 8's switch to `limited`.

  Only stub 1 gets a skeleton (deliberate scaffolding that fades through stubs 2–4 and disappears by the ★ stubs). Consider a sentence in `DESIGN_NOTE.md`.
- **Keep `metadata` on the environment.** I considered dropping it, since the linked docs don't mention it and only `cleanup.py` uses it, but it worked fine once I had the shape right. Maybe add one docstring line on *why* (cleanup on a shared key).

- ✅ *Done 2026-10-20: now `"vendor-vetting"` / `"vendor-vetter"`. Duplicate names are accepted on a shared key (tested); `check.py --solution` passes.* **Consider simplifying the environment name.** The stub docstring asks for `name: f"ma201-{state.handle()}"` (`lab/agent.py:28`, `lab/solutions/agent.py:20`), which reads as complex for no good reason. `cleanup.py` matches on `metadata` (`workshop` + `owner`), not on the name, so the handle in the name only helps tell environments apart in the Console on a shared key. Options: a plain literal like `"ma201-vetter"`, or keep the handle but explain why in the docstring. If changed, also update the agent name (`ma201-vetter-{handle}`, `agent.py:63` / `solutions/agent.py:40`) for consistency and rerun `check.py --solution`.
- **Files step (2) before Session step (4) feels out of order.** The docs show upload → mount as one flow ("Mounting files in a session": `resources=[{"type": "file", "file_id": ..., "mount_path": ...}]` on `sessions.create`). Options:
  - **(a) Reorder** ✅ *chosen* to env → agent → file → session, so the upload sits right before the mount. Keeps the create-once (env, agent, file) vs per-vet (session) split.
  - **(b) Merge** upload into `start_vet`. Matches the docs example, but either re-uploads on every vet or needs a `state.sync` inside `start_vet`, which muddies the once-vs-per-run lesson.
  - **(c) Move `upload_vendor` into `provided.py`** and let stub 4 teach the mount. One fewer stub. README already lists Files as a supporting *(Files)* concept.

  Touches `server.py:44-47,132`, `check.py` step numbers, `README.md:15-19,70-73`, `agent.py` / `solutions/agent.py` order.
- **Learners shouldn't need to open `provided.py`.** Stub 3 (and Claude Code) sent me to `provided.py` to look at `TOOLS`. It should feel like hidden plumbing. Make `agent.py` self-contained:
  1. **"What you're given" block** at the top of `agent.py`, replacing line 7. One plain line per imported name, e.g. `TOOLS` = `[{"type": "agent_toolset_20260401"}, RECORD_VERDICT]` (built-in sandbox tools + our one custom tool), `ENV_PACKAGES` = `{"type": "packages", "pip": ["pip-audit"]}` (pass as-is), `answer_custom_tool(session_id, event)` runs `record_verdict` locally and sends the result back.
  2. **Inline values only where the value is the concept.** Spell out `TOOLS` in stub 3. The `agent_toolset` entry is the point ("no tool executor for bash"). `SYSTEM` and the `RECORD_VERDICT` schema get a one-phrase description, not a copy.
  3. **Drop "in provided.py" from hints:** `agent.py:74, 117, 149, 174` and `README.md:72`. The names are already imported.
  4. **`lab/AGENTS.md`:**
     - Line 17: keep `provided.py` readable for debugging, but add a rule. When a participant asks what a constant or helper is, answer from `agent.py`'s glossary or in a sentence, and don't point them to `provided.py`.
     - Line 34: reword to "the imported helper `answer_custom_tool`".
  5. **Root `AGENTS.md` rule 4:** add "if a constant in `provided.py` changes, update the glossary at the top of `agent.py`" to guard against drift.
- **UI should frame progress by the four concepts and show what the server holds.** After stubs 1–3 the UI shows only checkmarks and id strings. Nothing shows that these are now real server-side resources. Proposal (plumbing only, so the learner's ~40 lines don't grow):
  1. **Group the left "Your stubs" column under the four concepts** (no separate bar on top, which would show progress twice). It lines up in stub order:

     | Stub | Function | Concept |
     |---|---|---|
     | 1 | `setup_environment()` | Environment |
     | 2 | `setup_agent()` | Agent |
     | 3 | `upload_vendor()` | Session (mounted resource) |
     | 4 | `start_vet()` | Session |
     | 5 | `run_vet()` | Events & reattach |
     | 6 | `find_open_session()` | Events & reattach |
     | 7 | `resume()` | Events & reattach |

     Stub 6 goes under Events & reattach, not Session, so the column reads as four sequential blocks in the same order as the slides.
  2. **Click or hover a concept to show its `retrieve` result.**
     - Environment: networking, packages (pays off in stretch 8).
     - Agent: version, model, tools (`agent_toolset` + `record_verdict`; pays off in stretch 9).
     - Session: status, resources, budget.
     - Events: lights up once streaming, with a count.

     Reinforces "the server is the source of truth," which stubs 6–7 rely on. Needs a small read-only endpoint in `server.py` + `static/` work.

  **Prerequisite:** the Files-step reorder (option a) above. Under the current order, Files sits between Environment and Agent and the grouping breaks.
- **Stub 5: unclear whether to send `user.custom_tool_result` or `user.tool_confirmation`.** The linked docs section ("Answer tool calls that pause the session") covers both pauses in one sentence. The rule:

  | Blocking event | Why | Reply |
  |---|---|---|
  | `agent.custom_tool_use` | your tool, runs in your process | `user.custom_tool_result` |
  | `agent.tool_use` / `agent.mcp_tool_use` | a permission policy wants approval | `user.tool_confirmation` (allow/deny) |

  The lab sets no permission policy, and `answer_custom_tool()` builds the reply anyway. The ★ is *when* to call it, so this question was a distraction from the real puzzle. Fixes:
  1. **`agent.py` stub 5:** add one line: "`answer_custom_tool()` sends the `user.custom_tool_result` for you. `user.tool_confirmation` is for permission policies, which this lab doesn't use."
  2. **UI stall banner** (`static/index.html:256`): show the blocking event type and expected reply, e.g. "Blocked on `agent.custom_tool_use` → expects `user.custom_tool_result`."
  3. **`session/likely-questions.md`:** add this Q&A with the table above.

  **Repeat of the `provided.py` finding:** when I asked Claude Code for help, it again pointed me to "Read `answer_custom_tool` in provided.py (line 115)." Second time in one run, so it's a pattern. Additions to that finding:
  - **`agent.py` must state each helper's contract where it's used**, not just its name. For example, in stub 5: "`answer_custom_tool(session_id, event)`: pass it the `agent.custom_tool_use` event; it runs `record_verdict` locally and sends `user.custom_tool_result`." The learner should never need the implementation, only the contract.
  - **`lab/AGENTS.md`:** make it an explicit rule: "Explain provided helpers by their contract (inputs, what they do, what they send). Don't send participants to `provided.py` or cite its line numbers unless they're debugging the helper itself."
  - **Good helper docstrings in `provided.py`** (inputs, effect, which event it sends), so hovering the name in VS Code shows the contract without opening the file.
- **Stub 5: not obvious that `answer_custom_tool` sends the event, so I wrote my own `events.send` too.** That duplicated the reply and had three bugs:
  - `event.send` instead of `events.send`.
  - A hard-coded `custom_tool_use_id` instead of `event.id`.
  - `result = answer_custom_tool(...)`, but the helper returns `None`.

  Fix: **show the helper's body in the stub 5 docstring.** It's ~8 lines, and the event shape plus `custom_tool_use_id = event.id` is itself a Managed Agents concept. It doesn't give away the ★ (*when* to call it). Proposed text:

  ```
  answer_custom_tool(session_id, event) does the "you run it" half for you.
  Pass it the agent.custom_tool_use event. It returns nothing. Inside, it does:

      text = <run record_verdict locally with event.input>   # saves .verdicts/<session>.json
      client.beta.sessions.events.send(session_id, events=[{
          "type": "user.custom_tool_result",
          "custom_tool_use_id": event.id,     # ← links the reply to the paused call
          "content": [{"type": "text", "text": text}],
      }])

  So you never build this event yourself. (user.tool_confirmation is for
  permission policies, which this lab doesn't use.) Your job: work out WHEN to call it.
  ```

  This replaces fix 1 of the earlier stub 5 finding (the one-line note), and it's the concrete form of the "state the helper's contract" fix in the `provided.py` finding. If `answer_custom_tool` changes, keep this docstring in sync (root `AGENTS.md` rule 4).
- **Each stub docstring should end with a "✅ Check" footer.** Today the only pointer is one line at the top of `agent.py`, and the per-stub checkpoints live in the README, while the learner is in `agent.py`. Use a fixed three-part footer, worded from `check.py`'s own `need()` messages:

  ```
  ✅ Check:  python check.py --step 1
     Passes when: env_… id is printed, a second call reuses it, pip-audit is pre-installed.
     In the app:  the stub turns green and environment_id appears below the rail.
  ```
  ```
  ✅ Check:  python check.py --step 5   (one full vet: ~1 min, ~5¢)
     Passes when: you answered the custom tool call, a verdict is saved locally,
                  and the turn ends with end_turn (not requires_action).
     In the app:  click Vet; the timeline ends on an end_turn badge and the
                  Verdict panel fills in.
  ```
  - **Stub 6 needs a warning:** `--step 6` deliberately crashes a vet and waits for it to park. Without a heads-up, that looks broken.
  - **Sync:** this is a third place describing each step (README, `check.py`, footer). Add it to root `AGENTS.md` rule 4, and update the step numbers if the file/agent reorder happens. The README checkpoints can then shrink to pointing at the footers.
  - It also helps the "UI looks empty after stubs 1–3" finding, since each footer says what *should* change on screen.
- **Stub 7: cite [Reconnect without missing events](https://platform.claude.com/docs/en/managed-agents/events-and-streaming#reconnect-without-missing-events).** It's the canonical docs pattern for exactly this stub (open stream → list history to seed seen ids → tail the stream, skipping seen) and is currently missing from the Docs list. Add it to the Docs list as-is. It answers the first two ★ questions (order, dedupe), and that's intended: the docs are there to help. The learner still works out the other two: rescuing the pending `record_verdict` from history, and not waiting if the turn already ended.
- **Stub 7 (reattach) is hard; consider a skeleton like stub 1's.** Placeholder from mid-run. Revisit after reading the full lab session log, which will show where I actually got stuck. Open questions for then:
  - How much structure to show (stream/list/dedupe frame) while keeping the two lab-specific parts (rescue the pending call, skip waiting if the turn ended) for the learner.
  - This changes the "scaffolding fades by the ★ stubs" idea from the stub 1 note. Maybe the fade should run across stubs 1–4 only, and the ★ stubs get structure but not answers.
- **Too much back-and-forth between surfaces; make Claude Code the hub.** I juggled the editor, the uvicorn terminal, Claude Code and the UI. I didn't use a separate `check.py` terminal; I ran checks through Claude Code with `! python check.py --step N`, and learners should do the same. Keep the UI from stub 1 onward: seeing elements kick in is the payoff, and the concept-grouping finding makes stubs 1–4 worth watching. Fix:
  - **`lab/AGENTS.md`:** Claude Code starts `uvicorn server:app --reload` in the background during setup and hands over the URL. When something fails, or the UI looks stale, it reads the server log itself (no copying tracebacks between windows). It also checks that `--reload` actually restarted after an edit.
  - **README + "✅ Check" footers:** show checks as `! python check.py --step N`, so the Claude Code loop is the documented path.
  - **Result: three surfaces, each with one job.** Editor (write the stub), Claude Code (help, checks, server, logs), browser (watch it come alive). Suggest VS Code with the Claude Code extension so the first two share a window.
- **Stub 8: docstring should say `config` still needs `"type": "cloud"`.** The hint "Fields you omit from config keep their current value" reads as if you can send only `networking`, but `type` is required on update too. It picks which config shape you're sending (`BetaCloudConfigParams.type: Required[Literal["cloud"]]` in the SDK; `solutions/agent.py:108` includes it). Reword to: "`config` must still say `"type": "cloud"`; other fields you omit (like packages) keep their current value."
- **Stub 9: unclear that you don't create sessions by hand.** "Then prove a session started BEFORE the update is still pinned to the old version" reads as part of `ship_v2`'s job, so I expected to create sessions myself. But `ship_v2` only updates the agent and returns the new version. `check.py` `c9` creates a session before calling it and another after, then compares `sessions.retrieve(...).agent.version`. Reword to: "Your function only updates the agent and returns the new version. You don't create any sessions. `! python check.py --step 9` starts one session before your update and one after, and shows the old one is still pinned." Keep the `sessions.retrieve(...).agent` hint as "how the check knows," not as a to-do.
- **Cleanup isn't the last step.** The README's cleanup (`README.md:151-152`) sits in Wrap-up, *before* the stretch goals, so anyone doing stubs 8–9 never sees it again. `agent.py` ends on the stretch goals with no cleanup at all. Fix:
  - **README:** add a final "Before you leave: tidy up" section after the stretch goals: `! python cleanup.py --dry-run`, then `! python cleanup.py`. Keep the Wrap-up one for people who skip the stretches.
  - **End of `agent.py`:** a closing "Done? Tidy up:" comment with the same two commands.
  - Use the `!` form (Claude Code loop) and plain `python` (venv active), not `../.venv/bin/python`, which is the authoring path. `lab/AGENTS.md:61` already covers "tidy up" requests.

### Added from the trial-run transcript (other session's wrap-ups)

- **SDK argument shapes tripped me up repeatedly.** Keyword vs positional, and the naming mismatches:
  - `sessions.create(agent=..., environment_id=...)`: one ends in `_id`, the other doesn't.
  - `sessions.list(...)` is keyword-only (`*` first), so a positional `agent_id` fails.
  - `environments.update(env_id, ...)` takes the id positionally, and `env_id=` fails.

  Fix: in each docstring, show call signatures in the form you type them (e.g. `client.beta.sessions.create(agent=..., environment_id=..., ...)`), not as prose. Consider a likely-questions entry on "the resource id goes first and positional; everything else is keyword".
- **Pages aren't lists.** `sessions.list` / `events.list` / `versions.list` return page objects. I chained `.order()` on one (stub 6) and passed one to `pending_custom_tool_calls`, which needs a real list (stub 7). Fix: stub 6–7 docstrings say "returns a page; iterate it, or wrap in `list(...)`".
- **Attribute vs method.** `.version()` twice and `.versions()` once in stub 9. Fix: the stub 9 docstring says "`agents.retrieve(id).version` (an int attribute)".
- **The `(filename, bytes, mime_type)` hint was read as code.** Fix: show the call shape, e.g. `client.beta.files.upload(file=("acme-csvkit.tar.gz", vendor_tarball(), "application/gzip"))`. Same "skeleton for the early stubs" idea as stub 1.
- **`check.py --step 6` hangs silently** when the stranded `record_verdict` isn't rescued, and it outlasts Claude Code's 120 s `!` timeout (moved to background), so it looks frozen. Fix: `check.py` prints progress while waiting ("waiting for the session to park… / waiting for your resume() to answer…") with a timeout and a hint ("did resume() answer the pending call from history?"). It also needs a note in the "✅ Check" footer and the Claude-Code-as-hub finding: long checks may need running from a normal terminal or with a longer timeout.
- **Stub 7 kept being checked with `--step 6`.** `check.py` already has `--step 7` as an alias for the same combined check (`STEPS` at `check.py:176`), but the README and Claude Code both said `--step 6`, so working on stub 7 felt off. Fix: stub 7's footer and the README say `--step 7` ("covers stubs 6 and 7 together").
- **Stub 5: replacing `turn_over` with an `end_turn` check** hangs the loop on other endings (terminated, retries exhausted). Fix: the docstring says "keep the `turn_over` check; add one case".

## Next steps

Moved to [`whats-left.md`](whats-left.md), the single to-do list.
