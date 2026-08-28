"""The evaluation report shape and its Markdown rendering — kept separate
from run.py so the report format is independently testable."""

from __future__ import annotations

from pydantic import BaseModel


class FieldAgentScenarioResult(BaseModel):
    name: str
    seeded: int
    matched: int
    recall: float
    extracted_total: int
    correctly_empty: bool
    cost_usd: float
    latency_s: float


class CartographerCaseResult(BaseModel):
    name: str
    expected_conflict: bool
    predicted_conflict: bool
    correct: bool
    detected_by: str
    cost_usd: float
    latency_s: float


class EvalReport(BaseModel):
    backend_name: str
    field_agent_results: list[FieldAgentScenarioResult]
    cartographer_results: list[CartographerCaseResult]

    @property
    def field_agent_mean_recall(self) -> float:
        if not self.field_agent_results:
            return 0.0
        return sum(r.recall for r in self.field_agent_results) / len(self.field_agent_results)

    @property
    def cartographer_accuracy(self) -> float:
        if not self.cartographer_results:
            return 0.0
        return sum(1 for r in self.cartographer_results if r.correct) / len(self.cartographer_results)

    @property
    def border_dispute_catch_rate(self) -> float:
        """Of the cases that SHOULD have been flagged as conflicts, how
        many actually were?"""
        should_conflict = [r for r in self.cartographer_results if r.expected_conflict]
        if not should_conflict:
            return 1.0
        caught = sum(1 for r in should_conflict if r.predicted_conflict)
        return caught / len(should_conflict)

    @property
    def false_annexation_rate(self) -> float:
        """Of the cases that should NOT have conflicted, how many were
        wrongly disputed anyway? (Not "false positive on conflict" in the
        usual sense — this is the cost of being too trigger-happy, which
        blocks legitimate annexations.)"""
        should_not_conflict = [r for r in self.cartographer_results if not r.expected_conflict]
        if not should_not_conflict:
            return 0.0
        wrongly_disputed = sum(1 for r in should_not_conflict if r.predicted_conflict)
        return wrongly_disputed / len(should_not_conflict)

    @property
    def total_cost_usd(self) -> float:
        return sum(r.cost_usd for r in self.field_agent_results) + sum(r.cost_usd for r in self.cartographer_results)

    @property
    def total_latency_s(self) -> float:
        return sum(r.latency_s for r in self.field_agent_results) + sum(r.latency_s for r in self.cartographer_results)

    def to_markdown(self) -> str:
        lines = [
            "# Atlas Evaluation Report",
            "",
            f"Backend: `{self.backend_name}`",
            "",
            "## Summary",
            "",
            "| Metric | Baseline (today's reality) | Atlas |",
            "|---|---|---|",
            f"| Cross-session fact recall | 0.0 (nothing persists) | {self.field_agent_mean_recall:.2f} |",
            f"| Border-dispute catch rate | n/a (no conflict detection today) | {self.border_dispute_catch_rate:.2f} |",
            f"| False-annexation rate | n/a | {self.false_annexation_rate:.2f} |",
            f"| Cartographer overall accuracy | n/a | {self.cartographer_accuracy:.2f} |",
            "",
            f"Total cost: ${self.total_cost_usd:.4f}  |  Total latency: {self.total_latency_s:.1f}s",
            "",
            "**Expedition Briefing effectiveness (held-out task) is not yet measured** — "
            "this requires running a fresh agent against a briefing-only bootstrap and "
            "scoring whether it avoids re-violating known constraints. Tracked in "
            "docs/requirements.md, not faked here.",
            "",
            "## Field Agent — per scenario",
            "",
            "| Scenario | Seeded | Matched | Recall | Extracted | Cost | Latency |",
            "|---|---|---|---|---|---|---|",
        ]
        for r in self.field_agent_results:
            note = " (correctly empty)" if r.correctly_empty else ""
            lines.append(
                f"| {r.name} | {r.seeded} | {r.matched} | {r.recall:.2f}{note} | {r.extracted_total} | ${r.cost_usd:.4f} | {r.latency_s:.2f}s |"
            )

        lines += [
            "",
            "## Cartographer — per case",
            "",
            "| Case | Expected | Predicted | Correct | Detected by | Cost | Latency |",
            "|---|---|---|---|---|---|---|",
        ]
        for r in self.cartographer_results:
            lines.append(
                f"| {r.name} | {r.expected_conflict} | {r.predicted_conflict} | {'✅' if r.correct else '❌'} | {r.detected_by} | ${r.cost_usd:.4f} | {r.latency_s:.2f}s |"
            )

        return "\n".join(lines) + "\n"
