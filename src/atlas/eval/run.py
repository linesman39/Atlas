"""The evaluation harness's single entrypoint: `python -m atlas.eval.run`.

Runs the Field Agent and the Cartographer against hand-authored, labeled
fixtures (eval/fixtures.py) using whatever LLMBackend is configured
(default: the free local one), scores the results (eval/metrics.py,
eval/report.py), and writes a JSON + Markdown report.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from atlas.agents.field_agent import extract_field_notes
from atlas.cartographer.evaluate import evaluate
from atlas.eval.cost_tracking import CostTrackingBackend
from atlas.eval.fixtures import CARTOGRAPHER_CASES, FIELD_AGENT_SCENARIOS
from atlas.eval.metrics import field_note_recall
from atlas.eval.report import CartographerCaseResult, EvalReport, FieldAgentScenarioResult
from atlas.llm import LLMBackend, get_default_backend
from atlas.models import AnnexationVerdict


def run_evaluation(backend: LLMBackend, backend_name: str) -> EvalReport:
    field_agent_results = []
    for scenario in FIELD_AGENT_SCENARIOS:
        tracked = CostTrackingBackend(backend)
        extracted = extract_field_notes(scenario.name, scenario.transcript_segment, backend=tracked)
        metrics = field_note_recall(extracted, scenario.seeded_notes)
        field_agent_results.append(
            FieldAgentScenarioResult(
                name=scenario.name,
                cost_usd=tracked.total_cost_usd,
                latency_s=tracked.total_latency_s,
                **metrics,
            )
        )

    cartographer_results = []
    for case in CARTOGRAPHER_CASES:
        tracked = CostTrackingBackend(backend)
        decision = evaluate(case.candidate, existing_facts=[case.existing], backend=tracked)
        predicted_conflict = decision.verdict == AnnexationVerdict.DISPUTED
        cartographer_results.append(
            CartographerCaseResult(
                name=case.name,
                expected_conflict=case.expect_conflict,
                predicted_conflict=predicted_conflict,
                correct=predicted_conflict == case.expect_conflict,
                detected_by=decision.resolved_by,
                cost_usd=tracked.total_cost_usd,
                latency_s=tracked.total_latency_s,
            )
        )

    return EvalReport(backend_name=backend_name, field_agent_results=field_agent_results, cartographer_results=cartographer_results)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Atlas's evaluation harness.")
    parser.add_argument("--out", type=Path, default=Path("results"), help="Directory to write the report into.")
    args = parser.parse_args()

    import os

    backend_name = os.environ.get("ATLAS_LLM_BACKEND", "local")
    try:
        backend = get_default_backend()
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Running Atlas evaluation against backend: {backend_name}")
    try:
        report = run_evaluation(backend, backend_name)
    except Exception as exc:
        print(f"error: evaluation run failed: {exc}", file=sys.stderr)
        print(
            "If this is a connection error, the local backend needs Ollama running "
            "(`ollama pull llama3.1`), or set ATLAS_LLM_BACKEND=claude for the hosted backend.",
            file=sys.stderr,
        )
        sys.exit(1)

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "eval_report.json").write_text(report.model_dump_json(indent=2))
    (args.out / "eval_report.md").write_text(report.to_markdown())

    print(report.to_markdown())
    print(f"Report written to {args.out}/eval_report.{{json,md}}")


if __name__ == "__main__":
    main()
