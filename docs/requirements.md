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

### 3. Chart Keeper / Atlas Keeper — ⏳ interface built, live annexation not yet exercised
- Must open an annexation as a reviewable pull request against a version-controlled Chart (per repo) or the Atlas (cross-repo), containing the candidate fact, its evidence, and the Cartographer's verdict. `GitHubAdapter.propose_annexation` implements this against the real GitHub API; the PR-formatting logic is unit-tested, the live API path is not yet exercised against a real repository.
- Must not merge without explicit Surveyor-General (human) approval — no auto-merge path.
- Chart and Atlas storage must be diffable and have history (so a Legend — a fact's provenance trail — is reconstructable after the fact). Satisfied by the markdown+YAML storage format being plain git-tracked files.

### 4. Briefing Agent — ✅ built (`src/atlas/agents/briefing_agent.py`)
- Must produce an Expedition Briefing on demand, drawing from the Chart and/or Atlas (not raw Field Notes). A human needs a readable narrative (`draft_briefing_for_human`); a fresh agent needs terse structured injection (`draft_briefing_for_agent`) — both implemented as genuinely different prompts, not the same text at two lengths.

### 5. The LLM layer must default to free and local — ✅ built (`src/atlas/llm/`)
- Must be backend-agnostic: every LLM-backed role takes an injectable `LLMBackend`, never hardcodes a specific provider.
- The default backend must incur zero cost and require no account or API key (`OllamaBackend`, talking to a local Ollama server over stdlib `urllib`).
- A hosted backend must be available as an explicit opt-in, never silently used (`ClaudeBackend`, selected via `ATLAS_LLM_BACKEND=claude`, installed via the `claude` extra so the base package doesn't require it).
- Engine dependencies (`pip install atlas-map`) must not pull in either PyGithub or claude-agent-sdk — both are optional extras.

### 6. Evaluation harness — ⏳ not yet built
- Must generate or load synthetic multi-session, multi-repo transcripts with seeded ground-truth facts at each tier, including deliberately planted border disputes.
- Must run both the baseline (static-CLAUDE.md-only) and the full Atlas pipeline against the same seeded scenarios.
- Must compute and report: per-tier fact recall, border-dispute catch rate, false-annexation rate, and Expedition Briefing effectiveness on a held-out task.
- Must be re-runnable by a third party from a clean environment — no hidden state, documented commands, documented expected output.

### 7. Non-functional requirements
- **Reproducibility**: every claimed result must trace to a command anyone can run themselves. ✅ the current test suite runs offline in under a second, no live model required.
- **Free by default**: the Engine must never require a paid account or API key to function. ✅ enforced by the packaging split and the local-first `LLMBackend` default.
- **Safety**: no consequential action (annexation) without human approval; no real/private data (synthetic transcripts only); credentials never enter the repo.
- **Cost/latency awareness**: the evaluation harness must be able to report tokens/latency/$ per iteration, not just correctness. The Claude backend cost-optimization finding (docs/architecture.md) is an example of the kind of result this should surface automatically.
- **Legibility**: Chart/Atlas contents and Expedition Briefings must be something a person would sign their name to, not an obvious raw dump.

## Explicitly not yet built (tracked in `docs/vision.md`)

- Map-style visualization UI (time-lapse, fault lines, trust coloring).
- MCP server exposing the Engine to any MCP client.
- Cross-organization trade routes.
- Autonomous weathering / scheduled re-verification of already-annexed facts.
- CODEOWNERS-style routing of annexation approval to a specific accountable Surveyor-General.
- Ask-the-Atlas natural-language query interface.

These stay explicitly named as direction, not claimed capability.

## Open questions, updated

- ~~What format Field Notes / Chart / Atlas are stored in~~ — resolved: markdown + YAML frontmatter, `src/atlas/storage.py`.
- ~~How the deterministic-first Cartographer check is implemented~~ — resolved: structured-field matching + `rapidfuzz`, `src/atlas/cartographer/deterministic.py`.
- How synthetic transcripts and their seeded ground truth are generated and kept honest (not hand-tuned to make Atlas look good) — still open, blocks the evaluation harness.
- Where the annexation PRs actually live — a dedicated repo per workspace, a branch convention, or something else — still open.
- What a genuinely free local model (e.g. Llama 3.1 8B via Ollama) actually achieves on Field Note extraction and conflict judgment quality compared to a hosted model — not yet measured; this is exactly what the evaluation harness should quantify once built, not assume.
