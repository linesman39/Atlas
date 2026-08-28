# Atlas — Project Definition (locked)

This is the locked project scope. For the unscoped ambition this draws from, see `docs/vision.md`. For the vocabulary used throughout, see `docs/lexicon.md`. For what's actually built versus still open, see `docs/requirements.md`.

## One-line

A team of agents that takes Field Notes on a live coding session, ground-truths what's worth keeping, and annexes it — through human-approved, pull-request-style sign-off — into a Chart (one repository's durable memory) and, from there, into the Atlas (a workspace's memory across repositories). The deliverable a person actually reads is the Chart/Atlas itself and an Expedition Briefing at handoff, not a black-box vector store.

## Who has this problem

A developer or team running long or repeated coding-agent sessions (Claude Code-style) on one or more repositories over time.

## The bottleneck, at three tiers

1. **Field Notes tier — context rot.** As a session grows, the harness compresses old turns to stay in-window. Compression is lossy: a constraint stated early, a rejected approach, a decision that later gets contradicted can silently drop out. Documented and formalized (Chroma's 2025 "context rot" research: every frontier model tested degrades as input grows, worst when facts sit mid-context).
2. **Chart tier — cross-session amnesia.** A fresh session on a repo it's worked before gets only a static, hand-written `CLAUDE.md`. Whatever a previous session painfully learned doesn't carry forward unless something explicitly charted it.
3. **Atlas tier — cross-repo blindness.** An agent working on one repo has no way to know a constraint or convention another repo's team already established. Multiple 2026 sources call this out as unsolved (`docs/competitive-landscape.md`): "workspace context and persistent memory are different things."

## Prior art and what Atlas differentiates on

Full detail in `docs/competitive-landscape.md` (six systems, official sources only). Summary: single-session-to-persistent-memory is solved and crowded (Letta, Mem0, Zep, Claude Code's own auto memory, Windsurf Memories, several MCP wrappers). Two gaps held up after checking primary sources directly:

1. **Only one of six systems reviewed (Zep/Graphiti) documents any contradiction-handling at write time.** The other five either accumulate without checking, defer to agent judgment with no stated check, or openly document arbitrary conflict resolution. Atlas's Cartographer is built specifically because this gap is real, not assumed.
2. **None of the six document a cross-repository tier.** This is the Atlas tier's reason to exist — the clearest, most consistent gap in the landscape.

Atlas adds two further differentiators, chosen from the wider vision as the ones concrete and demoable enough to build and evidence first:

3. **Ground-truthing, not assertion.** None of the six systems reviewed require a fact to be backed by reproducible evidence before it's stored — they store what an LLM extracted and said was true. Atlas's Cartographer refuses annexation without a linked artifact: a test result, a diff, a command's actual output.
4. **Annexation-as-pull-request.** Since Charts and the Atlas are git-versioned, an annexation opens as an actual PR — diffable, commentable, approved or rejected by a Surveyor-General — using the review muscle a team already has instead of a bespoke approval UI.

## Architecture — the five roles

- **Field Agent** — extracts structured Field Notes from the live session: decisions, constraints, files touched and why, abandoned expeditions, open questions.
- **The Cartographer** — checks new Field Notes against the existing Chart/Atlas at each annexation boundary. Deterministic/structured conflict check first (per the finding in `docs/competitive-landscape.md` that pure LLM-judged freshness tracking is unreliable), LLM judgment reserved for genuinely ambiguous cases. Requires ground-truthing evidence before approving an annexation; flags border disputes instead of silently overwriting.
- **Chart Keeper** — opens the annexation PR merging Cartographer-approved Field Notes into a repository's Chart; the durable, versioned, single-repository memory.
- **Atlas Keeper** — opens the annexation PR aggregating patterns and border disputes across multiple Charts into the workspace's Atlas.
- **Briefing Agent** — on demand, compresses the Chart/Atlas (not raw Field Notes) into an Expedition Briefing sized for whoever resumes next.

Fully autonomous pipeline. The human's only touchpoint is the Surveyor-General's approval on an annexation PR, and reading the Expedition Briefing at handoff — no human does any of the extraction, verification, or drafting.

## Baseline

Today's reality: a fresh session gets only the static, hand-written `CLAUDE.md` and none of the accumulated cross-session or cross-repo learning — no annexation, no ground-truthing, no cross-repo view. That's the manual-process baseline Atlas is measured against.

Internal ablation baseline (for the changelog): a naive single-shot "ask the LLM if this contradicts anything" Cartographer, replaced once the deterministic-first approach proves more reliable — kept in the changelog as a removed/superseded experiment, a record of what was tried and dropped, not only what worked.

## Data & evaluation

Fully synthetic multi-session, multi-repo transcripts (no real or private session data, by construction — see `docs/privacy.md`), seeded with facts at each tier plus intentional border disputes, using a category taxonomy adapted from LongMemEval-V2 (static facts, workflow knowledge, environment gotchas, premise awareness) for coding-agent sessions specifically.

**Primary metrics**:
- % of seeded facts correctly recalled, per tier, baseline vs. Atlas.
- Border-dispute catch rate at the Cartographer's gate (and false-annexation rate — bad facts that got annexed anyway).
- Expedition Briefing effectiveness: given only the briefing, does a fresh agent avoid re-violating known constraints on a held-out task, vs. a fresh agent given only the static baseline `CLAUDE.md`.

Chosen deliberately over borrowing a vendor-reported benchmark number: `docs/competitive-landscape.md` documents a live, unresolved dispute between Mem0 and Zep over whose numbers are correct, and a known flaw in the LOCOMO benchmark both cite. Self-controlled synthetic ground truth avoids inheriting either problem.

## Sources

See `docs/competitive-landscape.md` for the full source list underpinning the prior-art and differentiation claims above.
