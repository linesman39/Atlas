# Atlas

A team of agents that turns what a coding-agent session learns into durable, ground-truthed, cross-repository memory — instead of letting it die with the session.

**Free and local by default, the way git is free and local.** The engine — the data model, the Chart/Atlas storage, and every agent — runs entirely on your machine against a free local model (Ollama), no account and no API key required. GitHub integration and a hosted-model backend are optional upgrades you can turn on, the same way GitHub is an optional, paid, hosted layer built on top of git rather than something git itself needs. See `docs/architecture.md`, "Engine vs. Application."

Every fact Atlas records has to survive proof before it's trusted, and proof before it's trusted twice — before it moves from one session's Field Notes into a repository's Chart, and again before it moves from a Chart into the shared Atlas across a whole workspace. Nothing gets promoted on an LLM's say-so alone.

## Why

Long agent sessions lose things. Context gets compressed to fit the window and a constraint stated early quietly drops out. A fresh session on a repo it's worked before starts cold except for a static, hand-written `CLAUDE.md` — whatever the last session painfully learned doesn't carry forward. And an agent working on one repository has no way to know what another repository's team already learned the hard way. None of these are hypothetical — see [`docs/project-definition.md`](docs/project-definition.md) and [`docs/competitive-landscape.md`](docs/competitive-landscape.md) for the evidence, sourced from official documentation, papers, and repositories of the systems that already exist in this space (Letta, Mem0, Zep/Graphiti, Claude Code's own auto memory, Cognee, LangMem) — not assumed.

## How it's different

Two things, checked directly against six existing systems rather than assumed:

1. **Ground-truthing.** A fact isn't stored because an agent said so — it needs a linked test result, diff, or command output before it's eligible to be promoted at all. Five of the six systems reviewed store what an LLM extracted and asserted was true, with no evidence requirement.
2. **A cross-repository tier.** None of the six systems reviewed maintain memory across repositories — every one of them scopes to one deployment, one agent, or one project. Atlas's workspace tier (the Atlas proper) is built specifically because this gap is real.

Promotion itself — an *annexation*, in Atlas's own vocabulary — happens as a real, reviewable pull request, using the review discipline a team already has instead of a bespoke approval UI.

## The vocabulary

Atlas doesn't reuse git's terms (commit, branch, blame). It has its own, drawn from cartography: **Field Notes** (a session's raw record), **the Chart** (one repository's durable memory), **the Atlas** (a workspace's memory across repositories), **the Cartographer** (the agent that checks a new fact against everything already charted), **annexation** (a fact earning its way into the Chart or Atlas), **the Surveyor-General** (the accountable human who signs off). Full glossary: [`docs/lexicon.md`](docs/lexicon.md).

## Documentation

| Doc | What's in it |
|---|---|
| [`docs/project-definition.md`](docs/project-definition.md) | The locked scope: who has this problem, the three tiers, the five agent roles, baseline, evaluation. |
| [`docs/competitive-landscape.md`](docs/competitive-landscape.md) | Six existing agent-memory systems, researched from official sources only. |
| [`docs/lexicon.md`](docs/lexicon.md) | The full vocabulary. |
| [`docs/vision.md`](docs/vision.md) | The unscoped ambition — visualization, cross-org sharing, what this could become. |
| [`docs/requirements.md`](docs/requirements.md) | The functional spec each component is built against. |
| [`docs/architecture.md`](docs/architecture.md) | The technology decisions and why, for every layer including the ones not yet built. |
| [`docs/open-source.md`](docs/open-source.md) | License, governance, distribution. |

## Status

The Engine is built, tested, and working end to end: the data model, the Chart/Atlas storage format, the Cartographer's deterministic-first conflict check, and all three LLM-backed roles (the Field Agent, the Cartographer's escalation path, the Briefing Agent) — all running against a pluggable backend that defaults to a free local model. 37 tests pass, entirely offline, no live model or network call required (`tests/` uses a `FakeBackend` and mocked HTTP for the local backend's own tests). Application-layer pieces — the GitHub adapter's live PR-opening path, the MCP server, the visualization layer — are the next work; see [`docs/requirements.md`](docs/requirements.md) and [`docs/architecture.md`](docs/architecture.md).

## Running it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"        # the free engine only
pytest tests/ -v               # 37 tests, offline, no model required

# to actually run the agents against a real model:
ollama pull llama3.1           # once — the free local path
python3 scripts/live_smoke_test.py

# or, for the optional hosted backend instead:
pip install -e ".[claude]"
ATLAS_LLM_BACKEND=claude python3 scripts/live_smoke_test.py

# to enable GitHub annexation (optional, application-layer):
pip install -e ".[github]"
```

## License

Apache 2.0 — see [`LICENSE`](LICENSE). Rationale in [`docs/open-source.md`](docs/open-source.md).
