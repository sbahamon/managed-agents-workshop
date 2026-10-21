# Claude Managed Agents 201: session + hands-on lab

A workshop that takes engineers who've used the Messages API to the point where they've **shipped a working Managed Agents app**. It focuses on what sets Managed Agents apart: Anthropic runs the loop, the sandbox, and the session state, and your agent is a versioned resource on the server rather than code baked into your process.

| Part | Format | Time | Where |
|---|---|---|---|
| **Session: concepts** | HTML deck (single file, works offline, speaker notes on `N`) | ~12 min | [`session/slides.html`](session/slides.html) |
| **Session: live demo** | Jupyter/Colab notebook, "Repo health report" product backend | ~8 min | [`session/notebook/repo_health.ipynb`](session/notebook/repo_health.ipynb) |
| **Hands-on lab** | Python stubs + FastAPI + live event-timeline UI: vet an untrusted vendor package | 60 min | [`lab/README.md`](lab/README.md) |
| **Design note** | Judgment calls: model proposed → shipped → why | 5 min read | [`DESIGN_NOTE.md`](DESIGN_NOTE.md) |
| **Instructor hand-off guide** | One page: prep checklist, where learners get stuck, fallbacks. Appendix: [`session/likely-questions.md`](session/likely-questions.md) | 5 min read | [`INSTRUCTOR_GUIDE.md`](INSTRUCTOR_GUIDE.md) |

## Review it in 5 minutes

1. **Read** [`DESIGN_NOTE.md`](DESIGN_NOTE.md), the table at the top.
2. **Flip through** `session/slides.html` (open the file; arrow keys; press `N` for notes).
3. **Skim** the executed notebook. It's committed with outputs, so it renders on GitHub.
4. **See the lab without an API key:**
   ```bash
   python -m venv .venv && .venv/bin/pip install -r lab/requirements.txt
   cd lab && MA201_REPLAY=fixtures/events.jsonl ../.venv/bin/uvicorn server:app
   # open http://localhost:8000 and click "Vet acme-csvkit"
   ```
5. **Look at** `lab/agent.py` (what learners write) next to `lab/solutions/agent.py`.

## Run it for real (needs a key with Managed Agents access)

```bash
cp lab/.env.example lab/.env            # add ANTHROPIC_API_KEY and a MA201_HANDLE
cd lab
../.venv/bin/python check.py --solution # all core checkpoints vs the reference: ≈2 min, ≈10¢
../.venv/bin/python cleanup.py
```

Coding agents: see [`AGENTS.md`](AGENTS.md). If you're helping a participant, see [`lab/AGENTS.md`](lab/AGENTS.md).

*This is a take-home curriculum sample. The cohort and instructor are hypothetical. The API calls, costs and timings are real and were measured.*
