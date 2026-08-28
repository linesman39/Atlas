"""Local, adapter-free annexation.

For a solo or offline user, annexing a fact into a Chart doesn't need
GitHub at all — once the Cartographer approves it, annexation is just a
file write. This is the free engine's own annexation path, entirely
independent of adapters/github.py: no PR, no network, no account. The
GitHub adapter is an optional upgrade for teams who want reviewable
annexations; this module is what "it just works" means for everyone else.
"""

from __future__ import annotations

from pathlib import Path

from atlas.cartographer.evaluate import CartographerDecision, evaluate
from atlas.llm import LLMBackend
from atlas.models import AnnexationVerdict, Fact, FactStatus, Tier
from atlas.storage import read_all_facts, write_fact, write_index


def annex_locally(
    candidate: Fact,
    chart_dir: Path,
    use_llm_escalation: bool = True,
    backend: LLMBackend | None = None,
) -> CartographerDecision:
    """Evaluate a candidate fact against everything already in chart_dir,
    and if the Cartographer approves it, write it into the Chart and
    regenerate the index. Never writes anything for a DISPUTED or
    REJECTED_NO_EVIDENCE verdict — annexation only happens on approval."""
    existing = read_all_facts(chart_dir)
    decision = evaluate(candidate, existing_facts=existing, use_llm_escalation=use_llm_escalation, backend=backend)

    if decision.verdict == AnnexationVerdict.APPROVED:
        annexed = candidate.model_copy(update={"status": FactStatus.ANNEXED})
        write_fact(annexed, chart_dir)
        title = "The Atlas" if candidate.tier == Tier.ATLAS else "The Chart"
        write_index(read_all_facts(chart_dir), chart_dir, title=title)

    return decision
