# Competitive Landscape — AI Agent Memory Systems

Research conducted from official sources only: vendor documentation, official GitHub repositories, and papers authored by the tool's own team. Where a docs subdomain was unreachable, the GitHub README and/or the paper's own abstract (via arXiv/its official listing) was used instead — never third-party blogs or SEO aggregators. Every claim below is attributed to a specific source; where sources disagree, both are reported rather than picking one to state as fact.

---

## 1. Letta (formerly MemGPT)

**Approach**: Letta originates from the MemGPT research paper (Packer et al., Oct 2023, arXiv:2310.08560), which frames the problem as *"LLMs constrained by limited context windows, hindering their utility in tasks like extended conversations and document analysis"* and proposes **virtual context management** — an OS-inspired design that moves data between fast (in-context) and slow (out-of-context) memory tiers, using interrupts to manage control flow. The paper's evaluation domains were document analysis and extended conversation.

The company's currently shipped product, **Letta Code**, has evolved past the original paper's design: its GitHub repo describes agents that *"programmatically rewrite their context to improve and adapt over time, including system prompt learning (through memory blocks) and skill learning,"* with memory stored in **MemFS**, which *"sync[s] context to a custom GitHub repository"* — i.e., memory is git-versioned. The original `letta-ai/letta` repository is now explicitly described as *"a landing page for the Letta project"*; its archived V1 source is unsupported and "not suitable for production use."

**Tradeoffs**: Self-editing memory (the agent decides what to write) trades control for automation — the agent, not a deterministic rule, decides what's worth persisting. Git-backed memory (MemFS) gives auditability and versioning "for free" but ties memory to a git workflow.

**Achievements**: Established the tiered-memory framing (core/archival/recall) that much of the field still references. Apache-2.0 licensed.

**Where it's lacking / gap**: The public GitHub README for the current product does not document a session→durable-memory *verification* step — memory blocks are written by the agent's own judgment, with no stated conflict-detection mechanism before a fact is persisted. No workspace/cross-repo tier is described.

**Sources**: [github.com/letta-ai/letta](https://github.com/letta-ai/letta), [github.com/letta-ai/letta-code](https://github.com/letta-ai/letta-code), [arXiv:2310.08560](https://arxiv.org/abs/2310.08560)

---

## 2. Mem0

**Approach**: A "universal memory layer for AI Agents" using **single-pass ADD-only extraction** — per its own GitHub README, *"one LLM call, no UPDATE/DELETE. Memories accumulate; nothing is overwritten."* Retrieval is **multi-signal**: semantic (vector) matching, BM25 keyword search, and entity matching, "scored in parallel and fused," plus temporal reasoning to rank the right dated instance for a query. Storage is pluggable — local/file for the library mode, Docker + vector DB (Qdrant mentioned) for self-hosted, or a managed cloud platform.

**Tradeoffs**: ADD-only (never overwrite) sidesteps the hard problem of deciding when to delete/update a fact, at the cost of accumulating stale or superseded facts that retrieval scoring must rank around, rather than a system that actively resolves contradictions at write time.

**Achievements (per Mem0's own paper, arXiv:2504.19413)**: Reports 91% lower p95 latency and >90% token-cost savings vs. full-context baselines; 92.5 on LoCoMo and 94.4 on LongMemEval; a 26% relative improvement over an OpenAI memory baseline on an LLM-as-judge metric. **Contested**: the same paper reports Mem0 beating Zep on that judge metric (66.88 vs 65.99) — Zep has publicly disputed this methodology and the score attributed to it (see Zep entry). The paper itself flags that 446 of LOCOMO's questions expect "refusal" as the correct answer, but the standard benchmark harness drops those questions and instructs models never to abstain — a known weakness in the benchmark both vendors report against.

**Where it's lacking / gap**: No stated verification/contradiction-detection step at write time (by design — ADD-only). No workspace/cross-repo tier. Reported numbers are vendor-published and at least partly disputed by a competitor.

**Sources**: [github.com/mem0ai/mem0](https://github.com/mem0ai/mem0), [docs.mem0.ai/platform/overview](https://docs.mem0.ai/platform/overview) (via search-indexed content), [arXiv:2504.19413](https://arxiv.org/abs/2504.19413)

---

## 3. Zep / Graphiti

**Approach**: Zep's memory layer is built on **Graphiti**, an open-source **temporal knowledge graph engine**. Facts are stored as Entity→Relationship→Entity triplets, each carrying a **validity window** — per the GitHub repo, *"each fact... has a validity window: when it became true, and when (if ever) it was superseded."* Rather than deleting outdated facts, Graphiti **invalidates** them when new information contradicts them, while preserving full history so the graph can be queried "as of" any point in time. Every derived fact traces back to its source "episode" (raw ingested data) for provenance.

**Tradeoffs**: Explicit temporal modeling gives point-in-time queryability and a built-in contradiction-handling mechanism (supersession, not silent overwrite) — but at the cost of graph-construction complexity and a requirement for LLM providers with structured-output support (OpenAI, Anthropic, Gemini stated in the repo).

**Achievements (per Zep's own paper, arXiv:2501.13956)**: Reports beating MemGPT on the Deep Memory Retrieval benchmark (94.8% vs. 93.4%) and up to 18.5% accuracy improvement with 90% lower latency on LongMemEval vs. baseline implementations.

**Where it's lacking / gap**: No stated workspace/cross-repo tier. The GitHub repo does not publish independent benchmark numbers (only the linked paper does), and query latency claims ("sub-200ms at scale") are attributed to the managed platform, not the open-source Graphiti engine itself.

**Sources**: [github.com/getzep/graphiti](https://github.com/getzep/graphiti), [arXiv:2501.13956](https://arxiv.org/abs/2501.13956)

---

## 4. Claude Code native memory (Anthropic)

**Approach**: Two explicitly separate mechanisms, per Anthropic's own docs (code.claude.com/docs/en/memory, fetched directly): **CLAUDE.md files** (human-written, persistent instructions, loaded every session) and **auto memory** (Claude writes its own notes). Auto memory saves four typed categories only — `user`, `feedback`, `project`, `reference` — and explicitly *skips* anything derivable from the codebase or already stated in CLAUDE.md. Storage is a per-repository directory (`~/.claude/projects/<project>/memory/`) with an index file (`MEMORY.md`, capped at 200 lines / 25KB) and separate topic files loaded on demand. Memory is **machine-local** — not shared across machines — and both CLAUDE.md and auto memory are explicitly documented as *context, not enforced configuration*: "there's no guarantee of strict compliance."

**Tradeoffs**: The four-category cap and explicit "skip what's derivable" rule keep the memory index small and cheap to load, at the direct cost of scope — this is deliberately narrow (personal preferences and undiscoverable project facts), not a general knowledge store.

**Achievements**: The clearest, most precisely documented system reviewed — exact load limits, exact file locations, exact behavior on `/compact`, subagent memory isolation rules all specified.

**Where it's lacking / gap (stated explicitly in the docs, not inferred)**: Machine-local only, no cross-machine or cross-repo sharing. No conflict-detection step is documented — "if two rules contradict each other, Claude may pick one arbitrarily" is the stated behavior for CLAUDE.md, and nothing analogous is described for auto memory. No workspace tier across repositories.

**Sources**: [code.claude.com/docs/en/memory](https://code.claude.com/docs/en/memory) (fetched directly, official Anthropic documentation)

---

## 5. Cognee

**Approach**: An open-source "AI memory platform" combining vector embeddings, graph reasoning, and what its own materials call "cognitive-science-grounded ontology generation." Per its GitHub README, the pipeline runs: ingest → build a knowledge graph → expose four operations — **Remember** (store), **Recall** (query with automatic routing to the best search strategy), **Forget** (delete), and **Improve** (optional self-tuning based on conversation signals, "self-tune[s] its memory" after answered queries). Session memory syncs to the permanent graph in the background.

**Tradeoffs**: The explicit Remember/Forget API gives applications direct control over memory lifecycle (unlike Mem0's accumulate-only model), but the optional self-tuning "Improve" step means memory content can silently shift based on usage signals unless disabled.

**Achievements**: Reports 0.79 accuracy on the BEAM benchmark at 100K tokens, against a stated prior state-of-the-art of 0.735 and a RAG baseline of ~0.33 (vendor-reported, per GitHub README).

**Where it's lacking / gap (stated explicitly)**: The Postgres graph backend is *"explicitly marked a demo feature rather than production-ready, with production use requiring a licensed product"* — i.e., the fully open-source path is not the production-recommended path. No workspace/cross-repo tier described.

**Sources**: [github.com/topoteretes/cognee](https://github.com/topoteretes/cognee)

---

## 6. LangMem (LangChain / LangGraph)

**Approach**: Two complementary modes, per its GitHub README: **"hot path"** memory, where the agent manages its own memory during the conversation via explicit tools, and **background/"subconscious"** processing, where a separate memory manager "automatically extracts, consolidates, and updates agent knowledge" after the fact. Memories are organized into **namespaces** (e.g., `namespace=("memories",)`) for hierarchical separation by organization/user/application. Storage runs on LangGraph's storage primitives — in-memory for development, `AsyncPostgresStore` for production persistence.

**Tradeoffs**: Splitting hot-path and background memory formation avoids slowing down the live interaction for reflection/consolidation, at the cost of a lag between "something happened" and "it's durably stored and searchable."

**Achievements**: Framework-level flexibility — works with any storage backend LangGraph supports; MIT licensed, the most permissive license among the six.

**Where it's lacking / gap**: The README does not document any conflict-detection or contradiction-handling mechanism between hot-path and background-formed memories, nor between namespaces. No workspace/cross-repo tier. No published benchmark numbers were found in official sources (unlike Mem0, Zep, and Cognee).

**Sources**: [github.com/langchain-ai/langmem](https://github.com/langchain-ai/langmem)

---

## Synthesis — what this confirms about Atlas's scope

| System | Verification/conflict handling at write time | Cross-repo / workspace tier | Machine/scope portability |
|---|---|---|---|
| Letta (Letta Code) | Not documented | Not documented | Git-backed (portable via repo) |
| Mem0 | None by design (ADD-only, never overwrite) | Not documented | Deployment-dependent |
| Zep/Graphiti | Yes — temporal invalidation/supersession | Not documented | Managed platform or self-hosted |
| Claude Code auto memory | Not documented ("may pick one arbitrarily" for CLAUDE.md conflicts) | Not documented | Machine-local only, explicitly stated |
| Cognee | Explicit Remember/Forget API; optional self-tuning | Not documented | Backend-dependent |
| LangMem | Not documented | Not documented | Storage-backend-dependent |

Two findings hold up after checking primary sources directly, confirming the original project definition:

1. **Zep/Graphiti is the only one of the six with an explicit, documented contradiction-handling mechanism at write time** (temporal invalidation). Every other system either accumulates without checking (Mem0), defers to agent judgment with no stated check (Letta, Cognee's self-tuning), or documents its own uncertainty under conflict (Claude Code: "Claude may pick one arbitrarily"). This validates that a promotion gate with explicit verification is a real gap, not a strawman — five of six production/research systems reviewed don't document one.
2. **None of the six document a cross-repository/workspace tier.** Every system reviewed treats memory as scoped to one deployment, one agent, or one project. This is the clearest, most consistent gap across the entire landscape and is where Atlas's L3 (workspace) contributes something not found in any of the six official sources reviewed.

Additionally, the Mem0/Zep benchmark dispute and LOCOMO's known "446 refusal questions dropped" flaw are a direct, evidence-based argument for why Atlas's own evaluation (Part of `docs/project-definition.md`) uses fully synthetic, self-controlled ground truth rather than borrowing a vendor-reported number at face value.
