# Learner dry run (role-played agent, fresh copy, no solution access)

_Raw report below. The edits made in response are listed at the end._

Dogfood report: lab as a first-time Managed Agents learner (handle learner-dryrun). All checkpoints passed. Cleanup left nothing behind.

**Checkpoints:** 0 ✓ · 1 ✓ · 2 ✓ · 3 ✓ · 4 ✓ · 5 ✓ (BLOCK, risk 8) · 6/7 ✓ (headless check and a manual kill/restart test) · 8 ✓ · 9 ✓ (v1→v2) · full `check.py` ✓ (2m17s) · `cleanup.py` removed 8 sessions, the agent, the environment and the file. A second dry run showed nothing left.

**Time (actual / human estimate):**
- Setup: 0.5 / 5–8 min. pip install worked as written on Python 3.14.
- Stubs 1–4: 2 / 12–18 min. That's 4 docs pages plus SDK signatures, so 12 min is tight.
- Stub 5: 4.5 / 10–15 min. Most of it was watching the half-written run stall.
- Stubs 6–7: 3.7 / 15–20 min, including a 45 s wait.
- Stretch 8 and 9: 2 / 10–15 min.
- Wrap-up: 2.6 / 5 min.

**★ steps: both were pasteable.**
- **Stub 5:** watching the run stall at `requires_action` with `event_ids=[<custom_tool_use id>]` did take real thought. The fix didn't: the Python sample under the linked `#return-a-custom-tool-result` section is the same two lines (`if event.type == "agent.custom_tool_use": answer…`).
- **Stub 7:** the docstring (agent.py:156-163) spells out all four steps, including "SKIPPING events whose id you've already yielded". The linked reconnect section gives stream → list → tail as numbered steps with Python. README:138 points straight at it. Nothing is left to work out.

**Biggest finding: check 6 doesn't test what ★ #2 is about.** I ran a `resume()` that lists history *before* opening the stream and **never calls `pending_custom_tool_calls`**. `check.py --step 6` still passed every check.
- Why: c6_7 (check.py:120-123) "crashes" at the first `agent.tool_use` (about 2 s in) and sleeps 20 s. `record_verdict` only arrives at about 50 s, so the session is still `running` on reattach and the call shows up on the live stream. The answer-from-history branch never runs.
- My manual test (wait 45 s) did hit `idle · requires_action` and exercised that branch. So README:126 ("does the crash-and-reattach for you") oversells the check.
- Fix: poll `sessions.retrieve(sid).status == "idle"` before calling find/resume. The ordering bug is a race, so no check can catch it reliably. Say so.

**Confusion, mismatches and misleading hints:**
1. **agent.py:140:** stub 6's first link (`/managed-agents/sessions`) has no section on listing sessions. Only the API-reference link helped (`agent_id`, `order`, `statuses`).
2. **agent.py:185-186:** `#manage-environments` shows list, retrieve and archive, in cURL only. The page has no `environments.update` example at all. I found it with `dir()`/`inspect`, then had to test whether sending only `networking` in `config` keeps `packages`. It does (merge semantics). Put both facts in the hint.
3. **agent.py:197:** "updates need the current version". The docs (agent-setup "Update an agent") say `version` is optional and only enables optimistic concurrency.
4. **README:168:** "verdict gains a finding like *destination not reachable from sandbox*". In my run that showed up inside the beacon finding's evidence, not as a new finding.
5. **check.py:3** says "0-7"; README:146 says "0-6". Step 7 is an alias for step 6.
6. **Not in the README:** Part 5's half-written run leaves a session parked at `requires_action`. After stubs 6–7, the next `/api/reattach` silently picked it up and finished it (sesn_01Hq9…). A learner who reloads before doing the kill test sees a session they didn't start.
7. **Wording:** re-runs still print "environment created:" / "agent created:" even when the resource was reused (check.py:69, 83). Step 0 alone prints "All checkpoints passed."
8. **Event types:** the stream also emits `session.thread_status_idle` with the same `requires_action`. A learner keying off "status_idle" by substring could trip on it.

**Provided code:** no bugs found. One small note: `needs_attention` returns False for `rescheduling` (provided.py:146).

**Not verified:**
- I didn't open the browser UI. The grey rail, BLOCK card, 🛡 chip and ↻ tag were checked only through `/api/status` done flags, SSE event types, the egress regex in index.html:152 and the verdict JSON.
- Replay mode (README:62) couldn't be tested because fixtures were removed.
- The stub-5 stall run's time to reach `requires_action` wasn't measured: my curl ran to its 200 s timeout.

**Top 5 edits:**
1. Make c6_7 wait until the session is `idle` (requires_action) before reattaching, so the pending-answer path is actually tested. Soften README:126.
2. Make ★ #2 a real puzzle: drop step 4's "SKIPPING…" from agent.py:162-163, and don't spell out the order. For example, ask "what breaks if you list first?" and leave the reconnect link only in the README nudge.
3. agent.py:140: replace the `/sessions` link with the API-reference list page, and mention `statuses=`.
4. agent.py:185-186: name `client.beta.environments.update(env_id, config=…)`, say that `config` merges (packages survive), and fix the "needs the current version" wording at :197.
5. README Part 5/6: add one line, "your Part-5 session is still parked at requires_action; once stub 7 works, a reload will rescue it". Fix README:168 to say the unreachable-host result appears in the evidence.

---

## Edits made in response

| Finding | Change |
|---|---|
| Check 6 didn't exercise ★ #2: it reattached while the session was still running | `check.py` now waits until the session **parks idle at `requires_action`** with nobody listening, asserts nothing has answered it yet, and only then calls find and resume. Verified two ways: it passes against the solution, and it **fails** against a `resume()` that doesn't rescue the parked call |
| ★ #2 was pasteable from the docstring and the linked reconnect section | The docstring now asks four questions instead of listing steps, and links the general stream and list sections. The reconnect recipe moved to the README "stuck?" nudge and to a "compare *after* you've written yours" pointer |
| The ordering race is untestable | The README says so explicitly, so passing the check isn't mistaken for proof |
| Stub 6 link had no list section | Now links the `sessions.list` API reference and names `agent_id`, `order` and `statuses` |
| Stub 8 had no update example | Names `environments.update(env_id, config=…)`, explains that omitted fields are kept, and links the API reference |
| Stub 9 said "needs the current version" | Fixed: `version` is optional and only buys optimistic concurrency (a 409 on conflict) |
| README stretch 8 promised a separate finding | Now says "as its own finding, or inside the beacon finding" |
| The leftover parked session from Part 5 surprised the learner | Added a heads-up callout in Part 5 |
| `check.py` printed "created" on reuse and its docstring said 0–7 | Now prints "ready:" and says 0–6 |
| ★ #1's fix is a two-line match to the docs sample | **Kept on purpose.** The reasoning is in *diagnosing* the stall (which side runs the tool, what `event_ids` points to). Once diagnosed, the fix is meant to be easy. Noted in the design note |
| Timing: stubs 1–4 estimated at 12–18 min for a human vs 12 budgeted | Watch this in dogfooding. The likely trade is a shorter wrap-up. Logged for the instructor guide |
