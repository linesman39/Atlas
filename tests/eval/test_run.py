"""Wiring test: proves run_evaluation correctly drives the Field Agent
and the Cartographer across all fixtures and assembles a well-formed
report — without a live model. Uses ScriptedBackend, queuing exactly the
responses the fixtures are expected to trigger a backend call for.

Only 2 of the 5 CARTOGRAPHER_CASES are actually AMBIGUOUS (the rest
resolve deterministically, with no backend call at all) — this test's
call count is itself evidence that the deterministic-first design works:
5 total backend calls for 3 field-agent scenarios + 5 cartographer cases,
not 8.
"""

from atlas.eval.fixtures import CARTOGRAPHER_CASES, FIELD_AGENT_SCENARIOS
from atlas.eval.run import run_evaluation
from tests.fakes import ScriptedBackend


def test_run_evaluation_produces_a_result_per_fixture():
    responses = (
        ["[]"] * len(FIELD_AGENT_SCENARIOS)  # field agent: empty extraction is a valid response shape
        + ['{"conflict": true, "reason": "cannot both be true"}']  # ambiguous_genuine_conflict
        + ['{"conflict": false, "reason": "compatible addition"}']  # ambiguous_compatible_addition
    )
    backend = ScriptedBackend(responses)

    report = run_evaluation(backend, backend_name="scripted-test")

    assert len(report.field_agent_results) == len(FIELD_AGENT_SCENARIOS)
    assert len(report.cartographer_results) == len(CARTOGRAPHER_CASES)
    # exactly 5 backend calls: deterministic cases never touch the backend at all
    assert len(backend.calls) == 5

    by_name = {r.name: r for r in report.cartographer_results}
    assert by_name["deterministic_conflict"].detected_by == "deterministic"
    assert by_name["deterministic_conflict"].predicted_conflict is True
    assert by_name["ambiguous_genuine_conflict"].detected_by == "cartographer_llm"
    assert by_name["ambiguous_genuine_conflict"].predicted_conflict is True
    assert by_name["ambiguous_compatible_addition"].predicted_conflict is False


def test_report_renders_without_error():
    responses = ["[]"] * len(FIELD_AGENT_SCENARIOS) + [
        '{"conflict": true, "reason": "x"}',
        '{"conflict": false, "reason": "y"}',
    ]
    backend = ScriptedBackend(responses)
    report = run_evaluation(backend, backend_name="scripted-test")
    md = report.to_markdown()
    assert "scripted-test" in md
