# Atlas — Technology & Architecture

The organizing principle across every layer: **the core never talks to a hosting or rendering system directly — it talks to an adapter.** GitHub is the first substrate adapter, not a dependency baked into the design; the map UI is a client of the same data model everything else uses, not a special case. This document commits to a real technology for every layer, including the ones a hackathon-scoped build wouldn't need — because Atlas is meant to outlive the hackathon.

## Core (hackathon-critical)

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | One language across agent orchestration, data model, and evaluation harness; most reproducible for judges and, later, contributors, running from a clean environment. |
| Agent orchestration | Claude Agent SDK (Python) | The core roles (Field Agent, the Cartographer, Chart Keeper, Atlas Keeper, Briefing Agent) are built on the same primitives this project's own development session runs on. |
| Data model | Pydantic v2 | Facts are typed records (subject, claim, scope, evidence reference, confidence, tier), not prose — required for the Cartographer's deterministic check to be possible at all. |
| Storage format | Markdown + YAML frontmatter, one fact per file; a `CHART.md` / `ATLAS.md` index per tier | Modeled directly on Claude Code's own verified auto-memory pattern (`competitive-landscape.md`). Deliberately not a vector/graph DB (unlike Mem0, Zep, Cognee) — the requirement is diffable, git-native, human-legible, not semantic search at scale. |
| Deterministic conflict check | Structured-field matching + `rapidfuzz`, no embeddings | Same subject/scope key with a contradictory value is flagged cheaply before any LLM is invoked — keeps "deterministic-first" honest. |
| Substrate adapter | Abstract interface; `GitHubAdapter` is the first implementation | Chart Keeper and Atlas Keeper annex *through* this interface. Replacing or adding a hosting backend later is a second adapter, not a rewrite. |
| Annexation mechanism | Real GitHub PRs via the GitHub API | Uses the review muscle a team already has; makes the human-approval ground rule concrete. |
| Integration surface | MCP server, official `mcp` Python SDK | Any MCP client integrates, not just Claude Code — the concrete form of "substrate-agnostic on the agent side." |
| Evaluation harness | Plain Python, single entrypoint (`python -m atlas.eval.run`) | Generates/loads synthetic scenarios, runs baseline vs. Atlas, emits the four required metrics. |
| CI | GitHub Actions running the eval harness on every PR to Atlas's own repo | Dogfoods the same review discipline the annexation mechanism relies on. |

## Committed beyond the hackathon

**Weathering — not a new agent, the Cartographer on a schedule.** Re-verification of already-annexed facts (does the linked test still exist and pass, does the referenced code still exist) is the Cartographer invoked in a different mode via a scheduled GitHub Actions cron job, updating a `last_verified`/confidence field in the fact's frontmatter. Deliberately reusing the existing role instead of adding a sixth agent — the brief's own judging note that purposeful choices beat component count applies to Atlas's own design, not just the pitch.

**Trade routes — annexation across a repo boundary, not a new protocol.** A fact marked `shareable: true` by a Surveyor-General during annexation becomes eligible for export as a fork-and-PR into another org's Atlas, using GitHub's existing cross-org fork/PR federation rather than inventing a bespoke sharing protocol. Cross-org sharing is annexation with a wider audience, not a different mechanism.

**Ask-the-Atlas — a query tool, not a second source of truth.** Exposed as an MCP tool and a chat surface in the visualization frontend: natural-language question in, structured retrieval over the Pydantic fact store out, Claude synthesizes the answer — and every answer must cite a Legend. No answer without provenance, enforcing ground-truthing at query time the same way it's enforced at write time.

**CODEOWNERS-based Surveyor-General routing.** Annexation PRs parse the repo's existing `CODEOWNERS` (or a `.atlas/OWNERS.md` where fact categories don't map to file paths) and request review from the accountable human via GitHub's native reviewer-assignment API — reusing an existing primitive instead of building a custom routing system.

**Visualization layer**

| Layer | Choice | Why |
|---|---|---|
| Frontend | TypeScript + React | Standard, ecosystem-wide compatibility with the rendering libraries below. |
| Map rendering | deck.gl (WebGL) | Built for exactly this shape of problem — large-scale layered rendering with a geographic metaphor, arcs (trade routes), polygons (fault lines), heatmaps (weathering). |
| Layout computation | D3 (`d3-force` for topology, `d3-delaunay`/Voronoi for territory tessellation) | Converts the actual knowledge graph's real structure into map geography — regions are computed from real clustering, not decorative. |
| Serving layer | FastAPI (Python) | Parses the same markdown/YAML fact store the core already reads/writes; a `/history` endpoint replays `git log` for the time-lapse scrubber; a WebSocket endpoint pushes live fault-line and annexation events. |
| Client data fetching | TanStack Query | Standard caching/sync layer for the FastAPI endpoints. |
| Self-hosting | Docker Compose bundling the FastAPI service and the built frontend | `docker compose up` is the adoption story — reproducibility extends past the hackathon into real deployment. |

The visualization layer reads the same Chart/Atlas files the core agents write — it is a client of the data model, never a second copy of the truth.
