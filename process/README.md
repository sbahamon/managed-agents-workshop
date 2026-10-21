# Process artifacts

How this workshop was built with Claude Code (Opus 5.5) on 2026-10-19.

| File | What it is |
|---|---|
| `approved-plan.md` | The written plan that came out of brainstorming plus plan mode. It's the decision log *before* any code was written. |
| `learner-dry-run.md` | A role-played learner agent working through the lab from a fresh copy, with no solution access: friction, timings, edits made as a result |
| `session-logs/` | Exported Claude Code transcripts *(added by the author)* |

**Workflow:**
1. Three parallel research subagents covered the docs, the cwc workshops (and the `make-it-cheap` branch), and the claude-quickstarts.
2. A long run of `AskUserQuestion` rounds, under the superpowers *brainstorming* skill, settled the storyline, the shape, the scenario, the "work it out" steps, the stack and the session format.
3. In plan mode, a planning agent drafted the build, and an advisor review caught two problems: the notebook gave away the lab's reattach answer, and the reattach stub was too big.
4. Building started with spikes against the live API (key check, SBOM install, egress under `limited`, disconnect and reattach, file outputs). Then the lab solution came first, with stubs carved from it, then the notebook. The slides were built in parallel by a forked agent.
5. Verification: `check.py --solution`, a real kill-and-reattach in the browser, the notebook run both live and in replay mode, the learner dry run, and a post-hoc comparison against the reference repos.
