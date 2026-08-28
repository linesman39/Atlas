# Naming considerations — "Atlas"

Researched, not decided. This is information for you to weigh; renaming the project is your call, not mine to make unilaterally.

## What already uses "Atlas" in adjacent or overlapping space

- **MongoDB Atlas** — a major, trademarked commercial product (cloud database platform). The best-known "Atlas" in developer tooling generally. Not the same space, but the single most likely thing a developer thinks of on hearing the name.
- **ChatGPT Atlas** (OpenAI, 2026) — a browser product with a "remembers context from sites you visit" framing. Different product shape, but same company-recognition space (AI + "Atlas" + memory/context) as this project.
- **An MCP server literally named "Atlas," described as "AI Agent Long-Term Memory & Developer Knowledge Hub"** (listed on mcpmarket.com) — this is the closest, most concrete collision found: same category (agent memory), same name, same "developer knowledge" framing. Worth checking directly before any public announcement, since a judge, journalist, or early adopter searching "Atlas AI agent memory" would likely surface it alongside this project.
- **Atlaso** — a differently-spelled but same-space "memory layer for AI" product (Claude Code, Cursor, Codex, ChatGPT integrations).
- **Blazity's `atlas`** (GitHub) — an AI documentation/memory scaffold for coding agents. Different implementation, similar problem space, same name, on GitHub specifically — the exact platform this project's own repo lives on.
- **MITRE ATLAS** — an AI security threat-knowledge framework. Different domain (security, not memory), but shares the "AI-adjacent knowledge base" framing and is a name any AI-security-literate reader would recognize.

## The honest read

"Atlas" is not a coined or distinctive term here — it's a common English word already heavily used across exactly the two spaces this project sits at the intersection of (AI agent tooling, and long-term/persistent memory). At least one directly competing product (the mcpmarket.com listing) already occupies almost identical positioning under the identical name. This is a real, concrete risk to discoverability and to being confused with something else, not a hypothetical one.

## What this doesn't affect

None of this blocks anything already built — the code, the lexicon, the docs all work regardless of the final project name, since "Atlas" as a *concept* (the top tier, the compiled cross-repo memory) is the vocabulary choice discussed at length earlier, separate from "Atlas" as the *product/repo name*. If a rename ever happens, the lexicon documented in `docs/lexicon.md` (Field Notes, the Chart, the Cartographer, etc.) doesn't need to change — only the top-level product name would.

## Options, not a recommendation

- **Keep it.** Plenty of real products share a common word as a name and differentiate on substance; "Atlas" for agent memory isn't trademarked by any single party the way, say, a coined term could be.
- **Differentiate the name slightly** (as already done for the PyPI package: `atlas-cartographer` rather than the collision-prone `atlas-map`) while keeping "Atlas" as the product's public identity.
- **Rename outright** before any public announcement, while the cost of doing so is lowest (pre-launch, no external users depending on the name yet).

This is worth a deliberate decision before "ready for public announcement," not something to leave implicit.
