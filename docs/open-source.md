# Atlas — Open Source Commitments

This project is built to outlive the hackathon it started in. These are the commitments that make that real rather than aspirational.

## License

**Apache-2.0.** This matches every serious system reviewed in `competitive-landscape.md` (Letta, Mem0, Zep/Graphiti, Cognee are all Apache-2.0) and, unlike MIT, includes an explicit patent grant — important for something positioning itself as infrastructure other companies' engineering workflows will depend on.

## Governance

**Atlas governs itself using Atlas.** Changes to the fact schema, the tier-promotion rules, or the Cartographer's conflict logic go through the project's own annexation mechanism — proposed as a PR, ground-truthed with the reasoning and evidence for the change, reviewed by a Surveyor-General (a maintainer) before merge. This isn't a metaphor for the sake of consistency; it means the project's own decision history is stored exactly the way it asks every adopter to store theirs, and any adopter can inspect it as a working example.

**Contribution path**: a `CONTRIBUTING.md` documenting the same expectation — a change proposal is a Survey (evidence for why), not just a diff. A public roadmap, tracked as the project's own Atlas, rather than a separate planning document disconnected from the thing it's planning.

## Distribution

- **PyPI package** for the core library and MCP server, so `pip install` is the adoption path for the agent-facing pieces — no bespoke installer.
- **Docker image** bundling the FastAPI service and the built visualization frontend, so self-hosting the full stack is `docker compose up`, matching the reproducibility standard the hackathon evaluation itself is held to.
- **MCP registry listing** once that ecosystem's directory infrastructure matures, so Atlas is discoverable by any MCP client looking for a memory/context provider — not something you only find by knowing this hackathon happened.

## Why this matters beyond winning

The two gaps found in `competitive-landscape.md` — no verification gate at write time in five of six systems reviewed, and no cross-repository tier in any of them — aren't hackathon-convenient framings. They're gaps in tools real engineering teams are adopting right now, based on official vendor and research sources, not speculation. An open, adapter-based, evidence-grounded memory layer that isn't locked to one agent vendor is a real gap in real infrastructure. Treating this as a one-week demo would be the wrong scope for the problem it found.
