# Atlas — Technology & Architecture

Two organizing principles, and everything else follows from them:

1. **The core never talks to a hosting or rendering system directly — it talks to an adapter.** GitHub is the first substrate adapter, not a dependency baked into the design; the map UI is a client of the same data model everything else uses, not a special case.
2. **Engine and Application are separate, the way git and GitHub are separate.** git costs nothing, needs no account, and runs entirely on your machine. GitHub is an optional, better-resourced, hosted service built on top of it — valuable, but never required to use git at all. Atlas draws the same line: the **Engine** (the data model, the Chart/Atlas storage, the Cartographer, and the LLM-backed agents running against a free local model) works completely offline, for $0, forever. The **Application** layer (GitHub-hosted annexation, the MCP integration surface, the visualization web app) is optional, built on top of the free engine, and adds convenience and collaboration — not capability the engine lacks.

## The Engine — free, local, zero required dependencies on a paid service

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | One language across the data model, the Cartographer, and the LLM layer. |
| Data model | Pydantic v2 | Facts are typed records (subject, claim, scope, evidence reference, confidence, tier), not prose — required for the Cartographer's deterministic check to be possible at all. |
| Storage format | Markdown + YAML frontmatter, one fact per file; a `CHART.md` / `ATLAS.md` index per tier | Modeled directly on Claude Code's own verified auto-memory pattern (`competitive-landscape.md`). Deliberately not a vector/graph DB (unlike Mem0, Zep, Cognee) — the requirement is diffable, git-native, human-legible, not semantic search at scale. Plain files, so the engine needs no database server either. |
| Deterministic conflict check | Structured-field matching + `rapidfuzz`, no embeddings | Same subject/scope key with a contradictory value is flagged cheaply before any LLM is invoked — keeps "deterministic-first" honest, and needs no model at all for most cases. |
| LLM layer | Pluggable `LLMBackend` interface (`src/atlas/llm/`); **`OllamaBackend` is the default** | The Field Agent, the Cartographer's escalation path, and the Briefing Agent all run against whatever backend they're given, defaulting to a free local model via Ollama over stdlib `urllib` — no key, no account, no third-party HTTP dependency even. `ClaudeBackend` exists as an *optional* backend (installed via the `claude` extra) for a user who wants a hosted model's quality and is willing to pay — never the default, never assumed available. Selected via `ATLAS_LLM_BACKEND` (`local` or `claude`). |
| Packaging | `pip install atlas-cartographer` pulls in only `pydantic`, `PyYAML`, `rapidfuzz` | PyGithub and claude-agent-sdk are optional extras (`[github]`, `[claude]`) — installing the base package gets you a fully working, free engine with zero paid-service dependencies pulled in at all. |

**Cost finding worth keeping on record**: the Claude Agent SDK's default configuration loads a full skill/command/system-prompt set on every call — about $0.09 and ~22k cache-creation tokens overhead for a one-word reply. When `ClaudeBackend` is used, disabling `setting_sources`, `skills`, and default `tools`, and supplying a narrow system prompt, cuts that to ~$0.002 with no functional loss. Worth knowing even though it's not the default path, since it's the honest cost of the optional upgrade.

## The Application — optional, built on the Engine, the "GitHub" of the project

| Layer | Choice | Why |
|---|---|---|
| Substrate adapter | Abstract interface; `GitHubAdapter` is the first implementation, installed via the `github` extra | Chart Keeper and Atlas Keeper annex *through* this interface. Nothing in the Engine imports GitHub — a user who never installs the `github` extra can still run the Engine fully locally, annexing facts by hand (or a future native local adapter) with git alone. Replacing or adding a hosting backend later is a second adapter, not a rewrite. |
| Annexation mechanism | Real GitHub PRs via the GitHub API | Uses the review muscle a team already has; makes the human-approval ground rule concrete. Entirely optional — a solo user's local Chart is just files in a folder. |
| Integration surface | MCP server, official `mcp` Python SDK | Any MCP client integrates, not just Claude Code. |
| Evaluation harness | Plain Python, single entrypoint (`python -m atlas.eval.run`) | Generates/loads synthetic scenarios, runs baseline vs. Atlas, emits the required metrics — runs entirely against the Engine, no Application-layer dependency needed to evaluate it. |
| CI | GitHub Actions running the full test suite on every push | No test — Engine or Application — ever calls a live model or a live GitHub API. `tests/` uses a `FakeBackend`/`ScriptedBackend` and mocked HTTP for the local backend; the GitHub adapter's tests mock PyGithub's own objects (PyGithub itself is installed in CI to construct realistic exception/mock types, never to reach github.com). |

## Built beyond the original core (all ✅, see docs/requirements.md for status detail)

**Weathering — not a new agent, the Cartographer's evidence discipline on a schedule.** `src/atlas/weathering.py` re-checks already-annexed facts' evidence for continued existence (a `git cat-file -e` check for a `diff` reference, a file-existence check for a `test_result` reference) and marks a fact `DISPUTED` when its evidence has gone stale. Deliberately reuses the Cartographer's ground-truthing discipline instead of adding a sixth agent. Scope limit stated in the module itself: this checks existence, not whether a test still passes — a full re-run needs a CI job that knows the actual test framework.

**Trade routes — annexation across a repo boundary, not a new protocol.** `GitHubAdapter.propose_trade_route` exports a fact marked `shareable=True` as a fork-and-PR into another org's Atlas, reusing GitHub's existing cross-org fork/PR model rather than inventing a bespoke sharing protocol. Refuses non-shareable facts outright (tested).

**Ask-the-Atlas — a query tool, not a second source of truth.** `src/atlas/ask.py`, exposed as the MCP tool `ask_the_atlas`: natural-language question in, the configured LLM backend answers using only the charted facts given, and must cite the fact ids it relied on. No answer without provenance, enforcing ground-truthing at query time the same way it's enforced at write time. A chat surface in the future visualization frontend would be a client of this same function, not a separate implementation.

**CODEOWNERS-based Surveyor-General routing.** `src/atlas/codeowners.py` parses a repo's `CODEOWNERS` file and maps a fact's subject to the owners who'd be responsible for the synthetic path `GitHubAdapter` writes it under — and `propose_annexation` now calls it automatically after opening a PR, requesting review from the routed individual or team via GitHub's native reviewer-assignment API. Missing file, no match, or an invalid reviewer are all handled without failing the annexation itself.

**Visualization layer**

| Layer | Choice | Why |
|---|---|---|
| Frontend | TypeScript + React | Standard, ecosystem-wide compatibility with the rendering libraries below. |
| Map rendering | deck.gl (WebGL) | Built for exactly this shape of problem — large-scale layered rendering with a geographic metaphor, arcs (trade routes), polygons (fault lines), heatmaps (weathering). |
| Layout computation | D3 (`d3-force` for topology, `d3-delaunay`/Voronoi for territory tessellation) | Converts the actual knowledge graph's real structure into map geography — regions are computed from real clustering, not decorative. |
| Serving layer | FastAPI (Python) | Parses the same markdown/YAML fact store the Engine already reads/writes; a `/history` endpoint replays `git log` for the time-lapse scrubber; a WebSocket endpoint pushes live fault-line and annexation events. |
| Client data fetching | TanStack Query | Standard caching/sync layer for the FastAPI endpoints. |
| Self-hosting | Docker Compose bundling the FastAPI service and the built frontend | `docker compose up` is the adoption story. |

The visualization layer reads the same Chart/Atlas files the Engine writes — it is a client of the data model, never a second copy of the truth, and never required to use the Engine itself.
