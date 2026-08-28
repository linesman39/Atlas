"""Tests the Cartographer's full orchestration logic (ground-truthing ->
deterministic -> LLM escalation) without making a live LLM call — the
LLM escalation path is monkeypatched so this suite runs in CI, which has
no authenticated `claude` CLI. The live path itself is proven separately
in scripts/live_smoke_test.py (see docs/trajectories/)."""

import importlib

from atlas.cartographer.deterministic import CheckResult, DeterministicVerdict
from atlas.cartographer.evaluate import evaluate
from atlas.models import AnnexationVerdict, EvidenceKind, EvidenceRef, Fact

# atlas/cartographer/__init__.py does `from .evaluate import evaluate`, which
# shadows the `evaluate` submodule attribute on the `atlas.cartographer`
# package with the function of the same name. Fetch the real module via
# importlib rather than `import atlas.cartographer.evaluate as m`, which
# would resolve to that shadowed attribute instead of the module.
evaluate_module = importlib.import_module("atlas.cartographer.evaluate")


def _grounded(**kwargs) -> Fact:
    defaults = dict(evidence=[EvidenceRef(kind=EvidenceKind.DIFF, reference="abc", summary="")])
    defaults.update(kwargs)
    return Fact(**defaults)


def test_rejects_without_evidence():
    candidate = Fact(subject="x", scope="y", claim="z")  # no evidence
    decision = evaluate(candidate, existing_facts=[])
    assert decision.verdict == AnnexationVerdict.REJECTED_NO_EVIDENCE


def test_approves_new_territory():
    candidate = _grounded(subject="db_engine", scope="repo:a", claim="Uses Postgres.", value="postgres")
    decision = evaluate(candidate, existing_facts=[])
    assert decision.verdict == AnnexationVerdict.APPROVED


def test_disputes_deterministic_conflict_without_llm(monkeypatch):
    existing = _grounded(subject="db_engine", scope="repo:a", claim="Uses Postgres.", value="postgres")
    candidate = _grounded(subject="db_engine", scope="repo:a", claim="Uses Redis.", value="redis")

    def _fail_if_called(*args, **kwargs):
        raise AssertionError("LLM escalation should not be called for a deterministic conflict")

    monkeypatch.setattr(evaluate_module, "escalate_to_llm", _fail_if_called)

    decision = evaluate(candidate, existing_facts=[existing])
    assert decision.verdict == AnnexationVerdict.DISPUTED
    assert decision.dispute.detected_by == "deterministic"


def test_ambiguous_case_escalates_and_llm_approves(monkeypatch):
    existing = _grounded(subject="module:auth", scope="repo:a", claim="Uses session cookies.")
    candidate = _grounded(subject="module:auth", scope="repo:a", claim="Also supports JWT for the mobile client.")

    monkeypatch.setattr(
        evaluate_module,
        "escalate_to_llm",
        lambda cand, exist, backend=None: DeterministicVerdict(result=CheckResult.NO_CONFLICT, matched_fact_id=exist.id, reason="not mutually exclusive"),
    )

    decision = evaluate(candidate, existing_facts=[existing])
    assert decision.verdict == AnnexationVerdict.APPROVED


def test_ambiguous_case_escalates_and_llm_disputes(monkeypatch):
    existing = _grounded(subject="module:auth", scope="repo:a", claim="Uses session cookies.")
    candidate = _grounded(subject="module:auth", scope="repo:a", claim="Session cookies were removed entirely.")

    monkeypatch.setattr(
        evaluate_module,
        "escalate_to_llm",
        lambda cand, exist, backend=None: DeterministicVerdict(result=CheckResult.LIKELY_CONFLICT, matched_fact_id=exist.id, reason="mutually exclusive"),
    )

    decision = evaluate(candidate, existing_facts=[existing])
    assert decision.verdict == AnnexationVerdict.DISPUTED
    assert decision.dispute.detected_by == "cartographer_llm"


def test_ambiguous_case_without_llm_escalation_disputes_conservatively(monkeypatch):
    existing = _grounded(subject="module:auth", scope="repo:a", claim="Uses session cookies.")
    candidate = _grounded(subject="module:auth", scope="repo:a", claim="Also supports JWT.")

    def _fail_if_called(*args, **kwargs):
        raise AssertionError("LLM escalation should not be called when use_llm_escalation=False")

    monkeypatch.setattr(evaluate_module, "escalate_to_llm", _fail_if_called)

    decision = evaluate(candidate, existing_facts=[existing], use_llm_escalation=False)
    assert decision.verdict == AnnexationVerdict.DISPUTED
    assert decision.dispute.detected_by == "deterministic"
