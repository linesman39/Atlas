# Atlas — Open Source Commitments

## License

**Apache-2.0.** This matches every serious system reviewed in `competitive-landscape.md` (Letta, Mem0, Zep/Graphiti, Cognee are all Apache-2.0) and, unlike MIT, includes an explicit patent grant — important for something positioning itself as infrastructure other companies' engineering workflows will depend on.

**Dependency license compatibility — checked, not assumed** (`pip-licenses`, run against every direct dependency):

| Dependency | License | Note |
|---|---|---|
| pydantic, PyYAML, rapidfuzz, mcp, claude-agent-sdk, pytest, pytest-cov | MIT | No compatibility concern with Apache-2.0. |
| PyGithub | LGPL | Used only as an imported library (never vendored or statically embedded) — exactly the usage LGPL is designed to permit without requiring the consuming project to adopt LGPL itself. Worth flagging because it's the one non-MIT dependency, not because it's actually a problem. |

## Governance

**Atlas governs itself using Atlas.** Changes to the fact schema, the tier-promotion rules, or the Cartographer's conflict logic go through the project's own annexation mechanism — proposed as a PR, ground-truthed with the reasoning and evidence for the change, reviewed by a Surveyor-General (a maintainer) before merge. This isn't a metaphor for the sake of consistency; it means the project's own decision history is stored exactly the way it asks every adopter to store theirs, and any adopter can inspect it as a working example.

**Contribution path**: `CONTRIBUTING.md` documents the same expectation — a change proposal is a Survey (evidence for why), not just a diff.

## Distribution

- **PyPI package** (`atlas-cartographer` — `atlas-map` was already taken by an unrelated project; see `docs/naming-considerations.md`) for the Engine and the MCP server, so `pip install` is the adoption path — no bespoke installer. Verified to build cleanly and pass `twine check`, and the built wheel installs and runs correctly in a fresh environment (`docs/testing.md` covers the verification). Not yet actually published — that requires PyPI credentials this session doesn't have.
- **Docker image** bundling the Engine/MCP server (and, once built, the visualization frontend), so self-hosting is `docker compose up`.
- **MCP registry listing** once that ecosystem's directory infrastructure matures, so Atlas is discoverable by any MCP client looking for a memory/context provider.

## Why this matters

The two gaps found in `competitive-landscape.md` — no verification gate at write time in five of six systems reviewed, and no cross-repository tier in any of them — are gaps in tools real engineering teams are adopting right now, based on official vendor and research sources, not speculation. An open, adapter-based, evidence-grounded memory layer that isn't locked to one agent vendor is a real gap in real infrastructure.
