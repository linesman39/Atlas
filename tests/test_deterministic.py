from atlas.cartographer import CheckResult, check_deterministic
from atlas.models import Fact


def test_no_existing_fact_is_no_conflict():
    candidate = Fact(subject="db_engine", scope="repo:payments-api", claim="Uses Postgres.", value="postgres")
    verdict = check_deterministic(candidate, existing_facts=[])
    assert verdict.result == CheckResult.NO_CONFLICT


def test_matching_value_corroborates():
    existing = Fact(subject="db_engine", scope="repo:payments-api", claim="Uses Postgres.", value="postgres")
    candidate = Fact(subject="db_engine", scope="repo:payments-api", claim="Confirmed: Postgres.", value="postgres")
    verdict = check_deterministic(candidate, existing_facts=[existing])
    assert verdict.result == CheckResult.NO_CONFLICT
    assert verdict.matched_fact_id == existing.id


def test_differing_value_is_deterministic_conflict_no_llm_needed():
    existing = Fact(subject="db_engine", scope="repo:payments-api", claim="Uses Postgres.", value="postgres")
    candidate = Fact(subject="db_engine", scope="repo:payments-api", claim="Switched to Redis.", value="redis")
    verdict = check_deterministic(candidate, existing_facts=[existing])
    assert verdict.result == CheckResult.LIKELY_CONFLICT
    assert verdict.matched_fact_id == existing.id


def test_narrative_claims_are_ambiguous_not_falsely_resolved():
    existing = Fact(subject="module:auth", scope="repo:payments-api", claim="Auth module uses session cookies.")
    candidate = Fact(subject="module:auth", scope="repo:payments-api", claim="Auth module now uses JWT.")
    verdict = check_deterministic(candidate, existing_facts=[existing])
    assert verdict.result == CheckResult.AMBIGUOUS


def test_different_scope_is_not_a_conflict():
    existing = Fact(subject="db_engine", scope="repo:payments-api", claim="Uses Postgres.", value="postgres")
    candidate = Fact(subject="db_engine", scope="repo:reporting-api", claim="Uses Redis.", value="redis")
    verdict = check_deterministic(candidate, existing_facts=[existing])
    assert verdict.result == CheckResult.NO_CONFLICT


def test_fuzzy_subject_match():
    existing = Fact(subject="library: redis", scope="repo:payments-api", claim="Banned.", value="banned")
    candidate = Fact(subject="library:redis", scope="repo:payments-api", claim="Still banned.", value="banned")
    verdict = check_deterministic(candidate, existing_facts=[existing])
    assert verdict.result == CheckResult.NO_CONFLICT
    assert verdict.matched_fact_id == existing.id
