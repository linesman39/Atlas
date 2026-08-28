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
- Engine dependencies (`pip install atlas-cartographer`) must not pull in either PyGithub or claude-agent-sdk — both are optional extras.

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
- Exposes five tools: `record_field_note`, `propose_annexation`, `query_chart`, `get_briefing`, `ask_the_atlas`.
- `propose_annexation` uses local annexation (`local_annex.annex_locally`) by default — an MCP client gets a working, free annexation path with zero configuration, no GitHub required.
- Tested in-process via `server.call_tool` (`tests/test_mcp_server.py`) — no live transport or live model needed to verify the wiring is correct.

### 9. Weathering — ✅ built (`src/atlas/weathering.py`), honest scope limit
- Re-checks every fact in a Chart against real evidence: a `diff` reference is checked via `git cat-file -e` against a real repo checkout; a `test_result` reference is checked for the referenced file's existence. A fact where every checkable piece of evidence has gone stale is marked `DISPUTED`, not silently dropped — a human still decides whether to retract it.
- **Scope limit stated on purpose**: this checks whether evidence still *exists*, not whether a test still *passes* — a full re-run needs to know the project's test framework, which a generic library function can't. A CI-wired weathering job that actually re-executes tests and feeds the real pass/fail result in is future work; this is the framework-agnostic static check that works everywhere with zero configuration.

### 10. Ask-the-Atlas — ✅ built (`src/atlas/ask.py`, exposed via MCP)
- Answers a plain-language question using only the charted facts, and must cite the fact ids the answer relies on — ground-truthing enforced at query time, same discipline as at write time.

### 11. CODEOWNERS-based Surveyor-General routing — ✅ built and wired in (`src/atlas/codeowners.py`, `GitHubAdapter._request_codeowners_review`)
- Parses a `CODEOWNERS` file and maps a fact's subject to the same synthetic path `GitHubAdapter` writes it under, so routing matches what an annexation PR actually touches. Implements the common CODEOWNERS patterns (exact paths, directory prefixes, globs) via `fnmatch`, not GitHub's full pattern grammar — stated as a scope limit, not silently assumed complete.
- Wired into `GitHubAdapter.propose_annexation`: every annexation PR now automatically requests review from the routed owner(s), individual or team, via GitHub's native reviewer-assignment API. A missing `CODEOWNERS` file, no matching owner, or a routed owner GitHub rejects as an invalid reviewer are all handled by skipping the auto-request silently — routing is a convenience layered on an already-open PR, never something that blocks the annexation itself. Tested with mocked PyGithub objects (`tests/test_github_adapter.py`) covering all four cases; the live API call itself is not exercised against a real repository, same caveat as the rest of `GitHubAdapter`.

### 12. Trade routes — ✅ built (`GitHubAdapter.propose_trade_route`), not live-tested
- A fact must be marked `shareable=True` to be eligible — `propose_trade_route` refuses otherwise (tested). Reuses GitHub's own fork-and-PR cross-org contribution model rather than a bespoke sharing protocol: fork the target repo, branch, write the fact, open a PR back.
- Same live-testing caveat as the rest of `GitHubAdapter`: the PR-formatting logic is unit-tested, the live fork/PR path is not exercised against real repositories in this codebase's own test suite.

## Explicitly not yet built (tracked in `docs/vision.md`)

- Map-style visualization UI (time-lapse, fault lines, trust coloring) — a genuinely separate stack (TypeScript/React/deck.gl), not yet started.

These stay explicitly named as direction, not claimed capability.

## Open questions, updated

- ~~What format Field Notes / Chart / Atlas are stored in~~ — resolved: markdown + YAML frontmatter, `src/atlas/storage.py`.
- ~~How the deterministic-first Cartographer check is implemented~~ — resolved: structured-field matching + `rapidfuzz`, `src/atlas/cartographer/deterministic.py`.
- ~~Where does annexation actually happen without GitHub~~ — resolved: `src/atlas/local_annex.py`, a file write on Cartographer approval.
- How synthetic transcripts and their seeded ground truth are generated and kept honest — resolved for the current fixture set (hand-authored, `eval/fixtures.py`); still open for a larger, more varied scenario set as the project grows.
- Where the annexation PRs actually live — a dedicated repo per workspace, a branch convention, or something else — still open, blocks exercising `GitHubAdapter` live.
- What a genuinely free local model (e.g. Llama 3.1 8B via Ollama) actually achieves on Field Note extraction and conflict judgment quality compared to a hosted model — the harness can now measure this (`python -m atlas.eval.run`), but no run has been executed yet against a real local model in this environment (no Ollama installation available here) — the next person with Ollama installed should be the first real data point.
