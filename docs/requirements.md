# Atlas — Functional Requirements

This bridges `docs/project-definition.md` (locked scope) to the technology decisions in `docs/architecture.md`. States *what the system must do*; status markers below reflect what's actually built and tested versus what's next.

## Requirements

### 1. Field Agent — ✅ built (`src/atlas/agents/field_agent.py`)
- Must ingest a session transcript segment and extract structured Field Notes: decisions made, constraints stated, rejected approaches, open questions.
- Must run incrementally (new transcript segments → new Field Notes) rather than requiring the full session to be replayed each time.
- Output must be structured (not free text) so downstream roles can consume it programmatically.
- Must run against a pluggable `LLMBackend`, defaulting to the free local backend — never assume a paid API is available.

### 2. The Cartographer — ✅ built (`src/atlas/cartographer/`)
- Must accept a candidate fact and check it against the existing Chart/Atlas for contradiction.
- Must run a deterministic/structured check first (`deterministic.py`); escalate to LLM judgment only when the deterministic check is inconclusive (`llm_escalation.py`). Must log which path resolved each fact (`detected_by: "deterministic" | "cartographer_llm"`), for changelog/ablation comparisons.
- Must require at least one ground-truthing artifact (test result, diff, command output) attached to a candidate fact before it is eligible for annexation. A fact with no evidence is rejected, not silently annexed — enforced in `evaluate.py` before the conflict check even runs.
- On a detected border dispute, must not silently overwrite — must produce a flagged, human-legible description of the conflict for the Surveyor-General (`BorderDispute`, surfaced in the GitHub adapter's PR body).

### 3. Chart Keeper / Atlas Keeper
- **Local annexation — ✅ built and tested (`src/atlas/local_annex.py`)**: for a solo/offline user, annexation is just a file write once the Cartographer approves — `annex_locally()` runs the full Cartographer check and, on approval, writes the fact and regenerates the Chart index. No GitHub, no network, no account. This is the Engine's own annexation path.
- **GitHub annexation — ⏳ interface built, live PR-opening not yet exercised**: `GitHubAdapter.propose_annexation` implements the reviewable-pull-request path against the real GitHub API; the PR-formatting logic is unit-tested, the live API path is not yet exercised against a real repository (opening real branches/PRs needs a deliberate, permissioned test target, not something to do casually against whatever token is in an environment).
- Must not merge without explicit Surveyor-General (human) approval — no auto-merge path. Satisfied by construction: `annex_locally` never writes a DISPUTED or REJECTED_NO_EVIDENCE fact, and `GitHubAdapter` never merges its own PRs.
- Chart and Atlas storage must be diffable and have history (so a Legend — a fact's provenance trail — is reconstructable after the fact). Satisfied by the markdown+YAML storage format being plain git-tracked files.

### 4. Briefing Agent — ✅ built (`src/atlas/agents/briefing_agent.py`)
- Must produce an Expedition Briefing on demand, drawing from the Chart and/or Atlas (not raw Field Notes). A human needs a readable narrative (`draft_briefing_for_human`); a fresh agent needs terse structured injection (`draft_briefing_for_agent`) — both implemented as genuinely different prompts, not the same text at two lengths.

### 5. The LLM layer must default to free and local — ✅ built (`src/atlas/llm/`)
- Must be backend-agnostic: every LLM-backed role takes an injectable `LLMBackend`, never hardcodes a specific provider.
- The default backend must incur zero cost and require no account or API key (`OllamaBackend`, talking to a local Ollama server over stdlib `urllib`).
- A hosted backend must be available as an explicit opt-in, never silently used (`ClaudeBackend`, selected via `ATLAS_LLM_BACKEND=claude`, installed via the `claude` extra so the base package doesn't require it).
- Engine dependencies (`pip install atlas-map`) must not pull in either PyGithub or claude-agent-sdk — both are optional extras.

### 6. Evaluation harness — ✅ built (`src/atlas/eval/`), one metric still open
- Must generate or load synthetic scenarios with seeded ground-truth facts, including deliberately planted border disputes. Built as hand-authored fixtures (`eval/fixtures.py`) rather than LLM-generated, on purpose — see `eval/fixtures.py`'s docstring and `docs/project-definition.md`'s evaluation-integrity rationale.
- Must run both the baseline (nothing persists across sessions — 0.0 recall by definition) and the full Atlas pipeline against the same seeded scenarios. The report (`eval/report.py`) states the baseline explicitly rather than omitting it.
- Must compute and report: per-tier fact recall (`field_note_recall`), border-dispute catch rate, false-annexation rate — all built and tested (`tests/eval/`). Expedition Briefing effectiveness on a held-out task is **not yet implemented** — the report says so explicitly rather than faking a number.
- Must be re-runnable by a third party from a clean environment: `python -m atlas.eval.run`, writes `results/eval_report.{json,md}`. Runs against whatever `ATLAS_LLM_BACKEND` resolves to (free local by default).
- The harness's own test suite (`tests/eval/test_run.py`) proves a real property of the design, not just its own plumbing: of 8 total fixture cases, only 5 ever reach the LLM backend — the other 3 resolve deterministically for free.

### 7. Non-functional requirements
- **Reproducibility**: every claimed result must trace to a command anyone can run themselves. ✅ the current test suite runs offline in under a second, no live model required.
- **Free by default**: the Engine must never require a paid account or API key to function. ✅ enforced by the packaging split and the local-first `LLMBackend` default.
- **Safety**: no consequential action (annexation) without human approval; no real/private data (synthetic transcripts only); credentials never enter the repo.
- **Cost/latency awareness**: the evaluation harness must be able to report tokens/latency/$ per iteration, not just correctness. The Claude backend cost-optimization finding (docs/architecture.md) is an example of the kind of result this should surface automatically.
- **Legibility**: Chart/Atlas contents and Expedition Briefings must be something a person would sign their name to, not an obvious raw dump.

### 8. MCP integration surface — ✅ built (`src/atlas/mcp_server.py`)
- Exposes four tools: `record_field_note`, `propose_annexation`, `query_chart`, `get_briefing`.
- `propose_annexation` uses local annexation (`local_annex.annex_locally`) by default — an MCP client gets a working, free annexation path with zero configuration, no GitHub required.
- Tested in-process via `server.call_tool` (`tests/test_mcp_server.py`) — no live transport or live model needed to verify the wiring is correct.

## Explicitly not yet built (tracked in `docs/vision.md`)

- Map-style visualization UI (time-lapse, fault lines, trust coloring).
- Cross-organization trade routes.
- Autonomous weathering / scheduled re-verification of already-annexed facts.
- CODEOWNERS-style routing of annexation approval to a specific accountable Surveyor-General.
- Ask-the-Atlas natural-language query interface (the MCP surface above is the operational tools; a conversational query layer on top is separate).

These stay explicitly named as direction, not claimed capability.

## Open questions, updated

- ~~What format Field Notes / Chart / Atlas are stored in~~ — resolved: markdown + YAML frontmatter, `src/atlas/storage.py`.
- ~~How the deterministic-first Cartographer check is implemented~~ — resolved: structured-field matching + `rapidfuzz`, `src/atlas/cartographer/deterministic.py`.
- ~~Where does annexation actually happen without GitHub~~ — resolved: `src/atlas/local_annex.py`, a file write on Cartographer approval.
- How synthetic transcripts and their seeded ground truth are generated and kept honest — resolved for the current fixture set (hand-authored, `eval/fixtures.py`); still open for a larger, more varied scenario set as the project grows.
- Where the annexation PRs actually live — a dedicated repo per workspace, a branch convention, or something else — still open, blocks exercising `GitHubAdapter` live.
- What a genuinely free local model (e.g. Llama 3.1 8B via Ollama) actually achieves on Field Note extraction and conflict judgment quality compared to a hosted model — the harness can now measure this (`python -m atlas.eval.run`), but no run has been executed yet against a real local model in this environment (no Ollama installation available here) — the next person with Ollama installed should be the first real data point.
