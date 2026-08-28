# Atlas — Project Definition

## One-line

A verified, layered context map for AI coding-agent work — **session → codebase → workspace** — that gates what gets promoted to durable memory and hands a human-legible bootstrap brief to whoever resumes the work next.

## Who has this problem

A developer (or team) running long or repeated coding-agent sessions (Claude Code-style) on one or more repositories over time.

## The bottleneck, at three levels

1. **Session level — context rot.** As a session grows, the harness compresses old turns to stay in-window. Compression is lossy: a constraint stated early, a rejected approach, a decision that later gets contradicted can silently drop out. This is a documented, formalized phenomenon (Chroma's 2025 "context rot" research: every frontier model tested degrades as input grows, with facts buried mid-context hit hardest), not a one-off bug.
2. **Codebase level — cross-session amnesia.** A fresh session on a repo it's worked on before gets only a static, hand-written `CLAUDE.md`. Whatever a previous session painfully learned ("don't use library X, it broke prod," "this module has a non-obvious invariant") doesn't automatically carry forward unless a memory layer captured it.
3. **Workspace level — cross-repo blindness.** An agent working on repo B has no way to know a constraint or convention repo A's team already established. Multiple 2026 sources call this out explicitly as unsolved: *"workspace context and persistent memory are different things"* — no single context window or single-repo memory store holds both sides of a cross-repo dependency.

## Prior art (what already exists — do not rebuild)

- **Tiered/self-editing memory**: Letta (MemGPT) — core/archival/recall memory, agent self-edits what it stores.
- **Vector + graph memory layers**: Mem0 (vector-first, optional graph), Zep/Graphiti (temporal knowledge graph).
- **Native coding-tool memory**: Claude Code's own auto-memory (writes learnings back to CLAUDE.md between sessions), Windsurf's Cascade Memories.
- **Third-party memory MCP wrappers**: AgentMemory, Total Recall, kiro-memory, MemoryLake — all do "capture session → inject into next session."
- **Contradiction/conflict detection in memory**: AtomMem and related systems already run LLM/NLI-based conflict checks before writing a fact. Relevant finding: *"Don't Ask the LLM to Track Freshness: A Deterministic Recipe for Memory Conflict Resolution"* (arXiv 2606.01435) argues pure LLM-judged freshness tracking is unreliable and proposes a deterministic resolution recipe instead.
- **Evaluation methodology precedent**: LongMemEval-V2 (arXiv 2605.12493) evaluates long-term agent memory across five categories — static state recall, dynamic state tracking, workflow knowledge, environment gotchas, premise awareness — for web agents in customized environments.

**Conclusion**: single-session → persistent-memory is a solved, increasingly crowded problem. It is necessary plumbing for Atlas but not its contribution.

## Where Atlas puts its actual engineering effort

1. **A promotion gate, not a flat store.** Facts move Session → Codebase → Workspace only through an explicit verification step at each hop. A contradiction caught at session level is cheap; one that reaches workspace level poisons every future repo. The gate uses a deterministic/structured conflict check first, falling back to LLM judgment only for genuinely ambiguous cases — built and evaluated as an explicit iteration against a naive "just ask the LLM" version (kept in the changelog as a removed/superseded experiment).
2. **The workspace tier.** This is the layer the field agrees is still open. Atlas builds it directly: a Workspace Archivist aggregating patterns/conflicts across multiple codebase-level maps.
3. **A human-legible artifact, not a black box.** The deliverable is a readable map + a bootstrap brief generated on demand — not silent vector retrieval. This is what gets handed to the human at the single handoff point.

## Architecture

- **Session Mapper** — extracts structured facts (decisions, constraints, files touched + why, rejected approaches, open questions) from the live session.
- **Promotion Gate / Verifier** — checks new facts against existing ones at each promotion boundary (session→codebase, codebase→workspace); deterministic check first, LLM judgment for ambiguous cases; flags contradictions instead of silently overwriting.
- **Codebase Archivist** — merges gate-approved durable facts into a persistent, versioned map stored in the repo, surviving past any single session.
- **Workspace Archivist** — aggregates patterns and conflicts across multiple codebase-level maps.
- **Handoff Agent** — on demand, compresses the map (not the raw transcript) into a bootstrap brief sized for whoever resumes next (human or fresh agent).

Fully autonomous pipeline; the human's only touchpoint is reading/approving the final handoff artifact.

## Baseline

Today's reality: a fresh session gets only the static, hand-written `CLAUDE.md` and none of the accumulated cross-session or cross-repo learning — no promotion, no verification, no cross-repo view. This doubles as both the brief's "manual process" and "simple script" baseline categories.

Internal ablation baseline (for the changelog): a naive single-shot "ask the LLM if this contradicts anything" gate, replaced once the deterministic-first approach proves more reliable.

## Data & evaluation

Fully synthetic multi-session, multi-repo transcripts (avoids any real/private session data — ground rules 7/8), seeded with facts at each tier plus intentional contradictions, using a category taxonomy adapted from LongMemEval-V2 (static facts, workflow knowledge, environment gotchas, premise awareness) for coding-agent sessions specifically.

**Primary metrics**:
- % of seeded facts correctly recalled, per tier, baseline vs. Atlas.
- Contradiction catch rate at the promotion gate (and false-promotion rate — bad facts that got promoted anyway).
- Bootstrap-brief effectiveness: given only the brief, does a fresh agent avoid re-violating known constraints on a held-out task, vs. a fresh agent given only the static baseline `CLAUDE.md`.

## Sources

- [Context rot explained (& how to prevent it) — Redis](https://redis.io/blog/context-rot/)
- [Context Rot: How Increasing Input Tokens Impacts LLM Performance — Chroma](https://www.trychroma.com/research/context-rot)
- [Letta | Ry Walker Research](https://rywalker.com/research/letta)
- [The AI Agent Memory Landscape in 2026 — Feather DB](https://www.getfeather.store/theory/ai-agent-memory-frameworks-landscape-2026)
- [Mem0 vs Zep (Graphiti): AI Agent Memory Compared (2026)](https://vectorize.io/articles/mem0-vs-zep)
- [Zep: A Temporal Knowledge Graph Architecture for Agent Memory (arXiv 2501.13956)](https://arxiv.org/abs/2501.13956)
- [Windsurf Cascade Memories: Persist Context Across Sessions — MemNexus](https://memnexus.ai/blog/2026-02-20-windsurf-persistent-memory)
- [How Claude remembers your project — Claude Code Docs](https://code.claude.com/docs/en/memory)
- [Don't Ask the LLM to Track Freshness: A Deterministic Recipe for Memory Conflict Resolution (arXiv 2606.01435)](https://arxiv.org/pdf/2606.01435)
- [AtomMem: Building Simple and Effective Memory System for LLM Agents via Atomic Facts (arXiv 2606.19847)](https://arxiv.org/pdf/2606.19847)
- [Large-Repo Coding Agent Memory Bottleneck (June 2026) — Supermemory](https://supermemory.ai/blog/memory-bottleneck-large-repo-coding-agents/)
- [Remember Your Trace: Memory-Guided Long-Horizon Agentic Framework (arXiv 2605.14563)](https://arxiv.org/pdf/2605.14563)
- [LongMemEval-V2: Evaluating Long-Term Agent Memory (arXiv 2605.12493)](https://arxiv.org/abs/2605.12493)
