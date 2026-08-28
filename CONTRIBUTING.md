# Contributing to Atlas

## The short version

Open a PR. If it changes the fact schema, the tier-promotion rules, or the Cartographer's conflict logic, treat your own PR description the way Atlas asks every fact to be treated: state the claim, attach the evidence (why this change is correct — a test, a reproduction, a reasoned argument), and expect a maintainer (a Surveyor-General, in the project's own vocabulary — see `docs/lexicon.md`) to review it before merge. The project governs itself this way on purpose; see `docs/open-source.md`.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
```

## Ground rules

- **No untested claims.** If a module can be tested without live credentials (the data model, storage, the deterministic Cartographer check, adapter formatting logic), it must have tests that actually pass — see `tests/`. If a module genuinely needs a live LLM or API connection, say so explicitly in the module docstring rather than shipping something that looks implemented but isn't (see `src/atlas/agents/` for the pattern).
- **The adapter boundary is not optional.** Nothing outside `src/atlas/adapters/` may import or reference GitHub (or any other hosting system) directly. If your change needs to talk to a hosting system, it belongs behind `SubstrateAdapter`.
- **Read `docs/` before proposing an architectural change.** `docs/requirements.md` and `docs/architecture.md` explain what a component is supposed to do and why the current technology was chosen — a change that contradicts them should update the doc in the same PR, not silently diverge from it.
