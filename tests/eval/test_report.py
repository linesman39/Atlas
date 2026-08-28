from atlas.eval.report import CartographerCaseResult, EvalReport, FieldAgentScenarioResult


def _fa(name, recall, cost=0.01, latency=0.5):
    return FieldAgentScenarioResult(
        name=name, seeded=2, matched=int(recall * 2), recall=recall, extracted_total=2, correctly_empty=False,
        cost_usd=cost, latency_s=latency,
    )


def _cg(name, expected, predicted, detected_by="deterministic", cost=0.0, latency=0.1):
    return CartographerCaseResult(
        name=name, expected_conflict=expected, predicted_conflict=predicted, correct=(expected == predicted),
        detected_by=detected_by, cost_usd=cost, latency_s=latency,
    )


def test_mean_recall():
    report = EvalReport(backend_name="local", field_agent_results=[_fa("a", 1.0), _fa("b", 0.5)], cartographer_results=[])
    assert report.field_agent_mean_recall == 0.75


def test_border_dispute_catch_rate():
    results = [
        _cg("should_catch_1", expected=True, predicted=True),
        _cg("should_catch_2", expected=True, predicted=False),  # missed
        _cg("should_not_conflict", expected=False, predicted=False),
    ]
    report = EvalReport(backend_name="local", field_agent_results=[], cartographer_results=results)
    assert report.border_dispute_catch_rate == 0.5  # caught 1 of 2 real conflicts


def test_false_annexation_rate():
    results = [
        _cg("wrongly_disputed", expected=False, predicted=True),
        _cg("correctly_approved", expected=False, predicted=False),
    ]
    report = EvalReport(backend_name="local", field_agent_results=[], cartographer_results=results)
    assert report.false_annexation_rate == 0.5


def test_totals_sum_across_both_result_sets():
    report = EvalReport(
        backend_name="local",
        field_agent_results=[_fa("a", 1.0, cost=0.01, latency=1.0)],
        cartographer_results=[_cg("b", True, True, cost=0.02, latency=2.0)],
    )
    assert report.total_cost_usd == 0.03
    assert report.total_latency_s == 3.0


def test_markdown_report_is_well_formed_and_honest_about_gaps():
    report = EvalReport(backend_name="local", field_agent_results=[_fa("a", 1.0)], cartographer_results=[_cg("b", True, True)])
    md = report.to_markdown()
    assert "# Atlas Evaluation Report" in md
    assert "Baseline (today's reality)" in md
    assert "not yet measured" in md  # briefing effectiveness must not be faked
