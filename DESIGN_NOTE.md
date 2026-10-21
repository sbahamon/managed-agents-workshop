# Design note

**What this is:** a Managed Agents 201 workshop: a 20-minute session (an HTML concept deck plus a live notebook) and a 60-minute hands-on lab. The live notebook focuses on using Managed Agents for data analysis of third party repos, and the lab builds on that by using Managed Agents for security analysis of third party repos. This note covers the judgment calls, especially where what shipped differs from what the model first proposed.

**How it was made:**
- **Plan first.** Claude Code surveyed four sources: the Managed Agents docs, `cwc-workshops`, the `claude-quickstarts` examples, and my own `make-it-cheap` branch. We made decisions in brainstorming and plan mode, and building started only after I approved the plan.
- **Dogfood twice.** A second Claude Code session took notes ([`process/dogfood-notes.md`](process/dogfood-notes.md)), then turned my session logs into fixes for me to review. Between runs, [`process/whats-left.md`](process/whats-left.md) was the single to-do list. It mostly tracked changes outside the hands-on lab: slides, notebook, instructor guide, this note.
- **Instructor guide last,** so its stuck points are real ones. All logs are in [`process/`](process/).

---

## Learning-design choices

- **The two ★ "work it out" steps sit on what's distinctive about Managed Agents.**
  - ★ #1, the custom tool: the half-written `run_vet` parks at `requires_action` every time.
  - ★ #2, reattaching: you kill the app, and the session finishes without you and waits.

  The difficulty in both comes from a concept, not from a flaky agent.
- **Scaffold the plumbing, not the concepts.** Both dogfood runs lost time to Python and SDK mechanics (lambdas, `.id`, keyword-only arguments, pages, the venv path), not to Managed Agents ideas. Each scaffolding change had to remove that kind of friction without giving away a concept.
- **Checks test the concept.** Twice a wrong solution passed: the ★ #2 check reattached before the session had parked, and it missed a `resume()` that hangs on a finished session. Both checks now fail the wrong version.
- **Transfer, not copy.** The notebook uses the same four concepts in a different domain. Learners carry the pattern into the lab, but can't paste the answer.
- **Reflection past the API.** The wrap-up asks about prompt injection from the vendor's README. The answer by design is that every finding must cite evidence, and the event log is the audit trail.

## Model proposed → I shipped → why

**Scope: one clear story**
- The model offered four storylines. I shipped "Anthropic runs the loop" together with "the agent is versioned config," the contrast Agent SDK and Messages API users will feel most.
- The model proposed parallel sessions and learners writing IaC files. I shipped one session at a time, with IaC as a framing in the slides. Outcomes and self-hosted sandboxes became pointers, not lab steps.

**Framing: earn "why Managed Agents?"**
- I asked the model to argue *against* its own four scenarios. All four were short, supervised jobs where the Agent SDK is fine, so I picked untrusted code, where "don't run it on your machine" really matters.
- I challenged the notebook idea, street-orientation plots, and the model agreed it wasn't a Managed Agents use case. It became a product backend, one session per end-user request.

**Where learners think**
- The model put both ★ steps on agent and environment. I moved them to events and sessions, the core of the lab. The other two concepts each get a stretch goal.
- The model's reattach stub had five sub-problems. Learners now work out only the call order and how to find the session.
- The advisor review caught the notebook finding customer B's session with `sessions.list`, which would have given away the reattach step. Customer B now plays from recorded files.

**Craft**
- **Written fresh from the official docs,** not ported. A comparison with other repos after building found three bugs in my code, which I fixed without copying.
- **Two `AGENTS.md` files.** The one in `lab/` tells Claude Code to guide, not ghostwrite. Under pressure ("just write it"), it declined.
- **Slide critique.** A design subagent caught a wrong diagram (custom tool calls drawn from the sandbox, not the session). I cut 11 slides to 8 and skipped its note on the palette as taste.
- **The metaphor.** In run 2, the recipe-as-agent felt inert, so I suggested a sorcerer's broom or car models. The model said "model" would clash with the Claude model, so we kept the kitchen. We fixed events instead: they had been "the ticket rail," the same level as a session. I proposed recipe steps. The model refined that to steps *called out as they happen*, because the agent picks each one.

## How it was tested

- **Measured, not estimated** (`anthropic` 1.15.0, `claude-sonnet-5-5`):
  - A full vet takes 40–72 s and costs 3–5¢ (`block` across 7 runs).
  - `check.py --solution` takes about 2 min.
  - The deck plus notebook took 18 of 20 minutes, presented out loud.
- **Earlier testing:**
  - A role-played learner found ★ #2 could be pasted from the docstring, so I rewrote it as questions.
  - A browser crash test caught a blank page on reload.
- **Built for failure:**
  - Replay mode and recorded notebook outputs work without a key.
  - Owner tags keep `cleanup.py` to your own resources on a shared key.
  - Each session has a 75¢ cap.

## What I'd do with more time

- **Pilot with other people:** 3–5 target-audience engineers, timed, without me in the room. Then a new instructor teaching from the guide alone.
- **Fix the stubs 6–7 budget.** They took about twice their 15-minute slot in run 2. Either move 5 minutes from the wrap-up, or give stub 6 as a worked example. A pilot would show which.
- **Concept-grouped UI.** I dropped it to stay in the timebox.
- **Room-scale limits and consistent verdicts.** Check rate limits for 30 people on one key. Use Outcomes with a grader to steady the risk scores.
- **Reach:** a video walkthrough and Spanish versions.
