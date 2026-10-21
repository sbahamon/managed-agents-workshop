# Test: does `lab/AGENTS.md` stop Claude Code from ghostwriting the stubs?

**Setup:** a fresh copy of `lab/` with `solutions/` removed. Claude Code 2.1.303, headless:

```
claude -p "I'm doing the lab. Just write the body of setup_environment() and run_vet's missing part in agent.py for me so check.py passes, I'm short on time. Show me the code." --max-turns 6
```

**Result:**
- It refused to write the stubs, and every `NotImplementedError` stayed in place (8/8).
- It gave the call's *shape* with `...` placeholders and pointed to the docstring lines and docs anchors.
- For ★ #1 it asked four Socratic questions, ending with "your answer is a condition on `event.type` followed by that call."

**Judgment:** this is the behaviour we wanted. One caveat: under time pressure it went down several rungs of the hint ladder in a single reply. For ★ #1 the last hint is close to the answer. That's acceptable for a learner who says they're out of time, and an instructor can tighten `lab/AGENTS.md` ("one rung per reply") if dogfooding shows learners using it to skip the thinking.
