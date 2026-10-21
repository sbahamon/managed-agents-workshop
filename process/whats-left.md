# What's left

This is the only to-do list; `dogfood-notes.md` has the findings behind it. Updated 2026-10-20.

## Left: share it

- [ ] **Before making this repo public:** confirm with the recruiter that a public submission repo (without the prompt) is fine. Add the final session export to `process/session-logs/` after scanning it for brief quotes and personal details. This is a clean copy: no brief, and no raw build log.
- [ ] **Send to Workwell:** session, lab, guide, design note.

## Done

- **Dogfood run 2 (2026-10-20):**
  - The deck took 10 min (budget 12) and the notebook 8 (budget 8).
  - The lab took about 77 min on the clock, with a call and an internet drop. Details are in `dogfood-notes.md`.
- **Lab fixes from run 2,** on `lab-fixes-run2`. These are speed-ups, not structural changes:
  - a step 0 block
  - `.venv/bin/python` in every command
  - unique environment and agent names
  - long checks run through Claude Code
  - docstring fixes for stubs 1, 4, 5 and 6, plus the paging line
  - `check.py` now catches a cached `start_vet` and a `resume()` that hangs on a finished session, and prints `✗ expected: …`
- **Final test:** `check.py --solution` passes steps 0–6–7, 8 and 9. Replay mode loads with no key.
- **Hand edits:** `INSTRUCTOR_GUIDE.md` and `DESIGN_NOTE.md` are finished.
- **Design note restructured:** learning design first, then a conceptual change log, testing, and "What I'd do with more time". The open items moved there: the stubs 6–7 budget, the concept-grouped UI, a video walkthrough and Spanish versions.
- **Slides:** slide 4 now has events as the call-outs, and slide 8 has a readable lab crop.
- **`likely-questions.md`:** unverified claims are replaced with links to the docs.
- **Merged to `main`:** `dogfood-pass-1` (PR #1).
