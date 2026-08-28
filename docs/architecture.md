# Atlas — Technology & Architecture

Decided against `docs/requirements.md`. The organizing principle: **the core never talks to a hosting system directly — it talks to an adapter.** GitHub is the first adapter, not a dependency baked into the design. That's what makes "integrate with GitHub today, replace it later" an actual architectural property instead of a slogan.

## Stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | One language across agent orchestration, data model, and evaluation harness; most reproducible for judges running from a clean environment. |
| Agent orchestration | Claude Agent SDK (Python) | The five roles (Field Agent, the Cartographer, Chart Keeper, Atlas Keeper, Briefing Agent) are built on the same primitives this project's own development session runs on — subagents, tool use, orchestration. |
| Data model | Pydantic v2 | Facts are typed records (subject, claim, scope, evidence reference, confidence, tier), not prose — required for the Cartographer's deterministic check to be possible at all. |
| Storage format | Markdown + YAML frontmatter, one fact per file; a `CHART.md` / `ATLAS.md` index per tier | Modeled directly on Claude Code's own verified auto-memory pattern (index + topic files, see `competitive-landscape.md`). Deliberately not a vector/graph DB (unlike Mem0, Zep, Cognee) — the requirement is diffable, git-native, human-legible, not semantic search at scale. |
| Deterministic conflict check | Structured-field matching + `rapidfuzz`, no embeddings | Keeps "deterministic-first" honest — same subject/scope key with a contradictory value is flagged cheaply before any LLM is invoked. |
| Substrate adapter | Abstract interface; `GitHubAdapter` is the only implementation built for the hackathon | Chart Keeper and Atlas Keeper annex *through* this interface. Nothing upstream knows GitHub exists. Replacing GitHub later means writing a second adapter, not rewriting the Cartographer. |
| Annexation mechanism | Real GitHub PRs via the GitHub API (diff, evidence, Cartographer verdict attached) | Uses the review muscle a team already has; satisfies the human-approval ground rule concretely. |
| Integration surface | MCP server, official `mcp` Python SDK | Exposes record-field-note / query-chart / propose-annexation / get-briefing as MCP tools/resources, so any MCP client can integrate, not just Claude Code. |
| Evaluation harness | Plain Python scripts, single entrypoint (`python -m atlas.eval.run`) | Generates/loads synthetic scenarios, runs baseline vs. Atlas, emits JSON + Markdown report with the four required metrics. No framework overhead to reconstruct. |
| CI | GitHub Actions running the eval harness on every PR to Atlas's own repo | Dogfoods the same review discipline the annexation mechanism itself relies on. |

## Explicitly not decided yet

The visualization layer (`vision.md`) is out of hackathon scope (`requirements.md`), so no frontend stack is committed. When it's built it's a different concern entirely — most likely TypeScript/React with a canvas or WebGL map renderer — but deciding that now would be speculating past what the requirements actually call for.

## What this stack enables that the requirements demand

- **Reproducibility**: one language, one venv, one entrypoint per component.
- **Legibility**: Chart/Atlas contents are plain markdown, readable in a raw GitHub file view without any Atlas tooling running.
- **The "replace GitHub later" claim stays honest**: it's a second adapter implementing an interface that already exists, not a rewrite.
- **Substrate-agnostic on the agent side**: MCP exposure means the integration surface isn't Claude-Code-specific, matching the differentiation claim in `project-definition.md`.
