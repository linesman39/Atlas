# Atlas — Vision

This document is the north star, not the build spec. It is intentionally not scoped down. See `docs/requirements.md` for what actually gets built, and `docs/project-definition.md` for the locked scope.

## The core claim

Version control was built for an era where every line of code was hand-typed and therefore precious — so that's what got versioned: the line. In an agent-authored era, that inverts. An agent regenerates a hundred lines in seconds; lines are now cheap. What's actually scarce is the exploration that led to the *right* hundred lines — the dead ends ruled out, the evidence gathered, the constraint discovered the hard way. That's thrown away the instant a chat window closes. Atlas versions the thing that's actually expensive to produce, and treats code as a downstream projection of it: a Survey contains a diff, but the diff is not the Survey.

Taken all the way, this is a claim that Atlas isn't a memory add-on to the way software gets built — it's a candidate replacement for the substrate underneath it, the way git replaced diffing-and-emailing-patches. See `docs/lexicon.md` for the full vocabulary this rests on (Survey, Expedition, Annexation, the Cartographer, and so on).

**The honest tension**: git's genius is that it's a simple, content-addressed, purely mechanical object model — it ignores meaning entirely, which is exactly why it merges at planetary scale without a human or a model in the loop. Versioning reasoning instead of text gives up that mechanical cleanliness: reasoning doesn't hash deterministically, and resolving a border dispute needs judgment (the Cartographer), not a text-merge algorithm. The credible path is not "delete git" — it's Atlas's Surveys referencing git commits underneath for a long transitional period, git remaining the fast deterministic substrate for the cheap artifact (code) while Atlas becomes the substrate of record for the expensive one (why the code exists) — until the richer object model is trusted enough to be primary.

## Visualization — the Atlas as something you navigate, not read

- **A literal map.** Repositories as landmasses, modules as provinces, files as cities, dependencies as roads. Zoom out for the whole workspace Atlas; zoom in for one Chart's internal geography. Spatial layout is how people actually hold large structures in their head — nobody holds a 400-file dependency graph as a list.
- **A time-lapse scrubber.** Drag back through history and watch the map grow, Survey by Survey — watch a fact get charted in one Chart, then annexed into the Atlas weeks later. Watch untouched regions fade into fog of war as they weather.
- **Fault lines rendered live.** Unresolved border disputes as visible cracks, severity by depth, pulsing until a Surveyor-General closes them.
- **The Legend, clickable.** Click any charted fact, follow its trail back to the Survey and evidence that established it.
- **Trust coloring.** Facts shaded by confidence and freshness — vivid for something re-surveyed last week, weathered and pale for something untouched in months.

## Handoffs — beyond one human touching it once

- **Session → session**: an Expedition Briefing — narrative for a returning human, structured injection for a fresh agent.
- **Agent → agent, across vendors**: a parent agent spawns a subagent, or a team moves from one coding agent to another mid-project — Atlas hands over the relevant slice so switching tools doesn't mean starting cold. Requires Atlas to be substrate-agnostic (exposed via MCP), not locked to one agent framework, unlike every system reviewed in `docs/competitive-landscape.md`.
- **Person → person**: someone leaves, someone inherits an on-call incident — a real Expedition Briefing instead of tribal knowledge trapped in one head or six months of Slack.
- **Function → function**: hand security only the security-relevant slice of the Atlas; hand compliance only what compliance needs.
- **Org → org, via a trade route**: the acquisition-due-diligence case — a mature Atlas *is* a verified, evidence-linked account of what a codebase actually is, directly answering "is this repository actually good?" because the answer was already being assembled continuously rather than produced once for the sale.

## Beyond memory — what Atlas offers once it's infrastructure, not a feature

- **Anticipatory, not retrospective.** Interrupts an agent before it redoes something already tried and rejected, instead of only recording that it happened after the fact.
- **A real cost lever at org scale.** Every session today re-derives its understanding of a codebase from scratch. A mature Atlas turns that into a bootstrap — quantifiable token/time/dollar savings across an entire org, not one session.
- **An audit trail for regulated environments.** Ground-truthed, Chart-versioned, Surveyor-General-approved memory is exactly what "prove this AI-authored change was reviewed and why the agent believed X" requires.
- **A trust signal for AI-authored code.** "This repo has a mature, well-surveyed Atlas" becomes a legible quality signal in its own right — the difference between a codebase that's understood and one that's merely been generated.
- **A what-if simulator.** Before a risky change, an agent queries the Atlas: has anything like this been tried anywhere in the workspace, and what happened? Every agent gets the collective failure memory of every agent before it.
- **Ask-the-Atlas, in plain language.** Any teammate asks "why do we do it this way" and gets an answer traced to the Legend, instead of doing archaeology through git blame and old Slack threads.

## What's deliberately not built yet

The MCP server, trade routes, and weathering are real, tested code now, not just ambition — see `docs/requirements.md`. The one piece of this vision still entirely unbuilt is the visualization UI: a genuinely separate stack (TypeScript/React/deck.gl), not more of the same Python that everything else is. Purposeful sequencing, not scope-avoidance: the hardest, most defensible part of this vision (ground-truthed annexation with human sign-off, across the session→Chart→Atlas tiers, plus weathering, trade routes, and Ask-the-Atlas) was built first. See `docs/requirements.md` for exactly what's in and out.
