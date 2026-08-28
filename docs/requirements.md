# Atlas — Functional Requirements

This bridges `docs/project-definition.md` (locked scope) to a technology and structure decision. It states *what the system must do*, deliberately with no language/framework/storage choices yet — those come next, against this spec.

## In scope for the hackathon build

### 1. Field Agent
- Must ingest a session transcript (tool calls, file reads/writes, user turns, agent turns) and extract structured Field Notes: decisions made, constraints stated, files touched and why, abandoned expeditions (rejected approaches), open questions.
- Must run incrementally (new transcript segments → new Field Notes) rather than requiring the full session to be replayed each time.
- Output must be structured (not free text) so downstream roles can consume it programmatically.

### 2. The Cartographer
- Must accept a candidate fact (from Field Notes, or from a Chart being considered for Atlas-tier annexation) and check it against the existing Chart/Atlas for contradiction.
- Must run a deterministic/structured check first; escalate to LLM judgment only when the deterministic check is inconclusive. Must log which path was used, per fact, for the changelog's ablation comparison.
- Must require at least one ground-truthing artifact (test result, diff, command output) attached to a candidate fact before it is eligible for annexation. A fact with no evidence is rejected, not silently annexed.
- On a detected border dispute, must not silently overwrite — must produce a flagged, human-legible description of the conflict (what's old, what's new, why they conflict) for the Surveyor-General.

### 3. Chart Keeper / Atlas Keeper
- Must open an annexation as a reviewable pull request against a version-controlled Chart (per repo) or the Atlas (cross-repo), containing: the candidate fact, its ground-truthing evidence, and the Cartographer's verdict.
- Must not merge without explicit Surveyor-General (human) approval — no auto-merge path, per the hackathon's own ground rule on human approval before consequential action.
- Chart and Atlas storage must be diffable and have history (so a Legend — a fact's provenance trail — is reconstructable after the fact).

### 4. Briefing Agent
- Must produce an Expedition Briefing on demand, drawing from the Chart and/or Atlas (not raw Field Notes), sized appropriately for the target (a fresh agent needs structured injection; a human needs a readable narrative — both must be supported, even if only one is fully polished for the hackathon demo).

### 5. Evaluation harness
- Must generate or load synthetic multi-session, multi-repo transcripts with seeded ground-truth facts at each tier, including deliberately planted border disputes.
- Must run both the baseline (static-CLAUDE.md-only) and the full Atlas pipeline against the same seeded scenarios.
- Must compute and report: per-tier fact recall, border-dispute catch rate, false-annexation rate, and Expedition Briefing effectiveness on a held-out task.
- Must be re-runnable by a third party from a clean environment (ground rule 10) — no hidden state, documented commands, documented expected output.

### 6. Non-functional requirements
- **Reproducibility**: every claimed result must trace to a command a judge can run themselves.
- **Safety/ground rules compliance**: no consequential action (annexation) without human approval; no real/private data (synthetic transcripts only); credentials never enter the repo.
- **Cost/latency awareness**: the changelog needs real numbers (tokens, latency, $) for baseline vs. Atlas at each iteration — the harness must be able to report these, not just correctness.
- **Legibility**: Chart/Atlas contents and Expedition Briefings must be something a person would sign their name to, not an obvious raw dump — this is a judged criterion (End to End Quality), not a nice-to-have.

## Explicitly out of scope for the hackathon build (tracked in `docs/vision.md`)

- Map-style visualization UI (time-lapse, fault lines, trust coloring).
- Substrate-agnostic MCP exposure so third-party agents (Cursor, Devin, etc.) can read/write the same Atlas.
- Cross-organization trade routes.
- Autonomous weathering / scheduled re-verification of already-annexed facts.
- CODEOWNERS-style routing of annexation approval to a specific accountable Surveyor-General.
- Ask-the-Atlas natural-language query interface.

These stay explicitly named as direction, not claimed capability — the README and video should be able to point at this list and say "here's the ceiling, here's what's proven" without either overclaiming or hiding the ambition.

## Open questions to resolve during technology/structure planning

- What format Field Notes / Chart / Atlas are stored in (must be diffable, git-friendly, and human-legible per the requirements above).
- How the deterministic-first Cartographer check is implemented (rule-based? structured extraction + exact/fuzzy match? something else) versus when it escalates to an LLM.
- How synthetic transcripts and their seeded ground truth are generated and kept honest (not hand-tuned to make Atlas look good).
- Where the annexation PRs actually live — a dedicated repo per workspace, a branch convention, or something else.
