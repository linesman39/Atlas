from atlas.models import EvidenceKind, EvidenceRef, Fact, Tier


def test_fact_defaults():
    fact = Fact(subject="library:redis", scope="repo:payments-api", claim="Do not use Redis for session storage.")
    assert fact.tier == Tier.FIELD_NOTES
    assert fact.confidence == 0.5
    assert fact.is_ground_truthed() is False


def test_fact_with_evidence_is_ground_truthed():
    fact = Fact(
        subject="library:redis",
        scope="repo:payments-api",
        claim="Do not use Redis for session storage — it dropped sessions under load.",
        evidence=[EvidenceRef(kind=EvidenceKind.TEST_RESULT, reference="tests/test_sessions.py::test_load", summary="failed under 500 concurrent sessions")],
    )
    assert fact.is_ground_truthed() is True


def test_fact_ids_are_unique():
    a = Fact(subject="x", scope="y", claim="z")
    b = Fact(subject="x", scope="y", claim="z")
    assert a.id != b.id
