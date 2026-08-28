# Atlas

A team of agents that turns what a coding-agent session learns into durable, ground-truthed, cross-repository memory — instead of letting it die with the session.

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

Early. The core data model, the Chart/Atlas storage format, and the Cartographer's deterministic conflict check are built and tested (`src/atlas/`, `tests/`). The LLM-backed pieces — the Field Agent's extraction, the Cartographer's escalation path for ambiguous conflicts, the Briefing Agent — are real interfaces (`src/atlas/agents/`) not yet wired to a live model. See [`docs/requirements.md`](docs/requirements.md) for what's built versus what's next.

## Running the tests

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
```

## License

Apache 2.0 — see [`LICENSE`](LICENSE). Rationale in [`docs/open-source.md`](docs/open-source.md).
