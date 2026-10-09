"""Deterministic rules engine with reproducible Pass/Fail/Warning/Unknown/N/A."""

from __future__ import annotations

from typing import List, Optional

# Schemas are imported lazily-compatible; agent/rules live at repo root.
from app.models.schemas import (
    Architecture,
    CategoryScores,
    EvaluationFinding,
    Requirements,
    RuleStatus,
    ScoreReport,
)
from rules.best_practice_rules import BestPracticeRules
from rules.cost_rules import CostRules
from rules.reliability_rules import ReliabilityRules
from rules.scalability_rules import ScalabilityRules
from rules.security_rules import SecurityRules


STATUS_SCORE = {
    RuleStatus.PASS: 100.0,
    RuleStatus.WARNING: 60.0,
    RuleStatus.FAIL: 0.0,
    RuleStatus.UNKNOWN: 50.0,
    RuleStatus.NOT_APPLICABLE: None,
}

DEFAULT_WEIGHTS = {
    "security": 0.30,
    "cost": 0.15,
    "reliability": 0.25,
    "scalability": 0.15,
    "best_practices": 0.15,
}


def score_findings(
    findings: List[EvaluationFinding],
    weights: Optional[dict] = None,
) -> ScoreReport:
    """Compute category and overall scores from findings (0-100)."""
    weights = weights or DEFAULT_WEIGHTS
    by_category: dict[str, List[EvaluationFinding]] = {
        "security": [],
        "cost": [],
        "reliability": [],
        "scalability": [],
        "best_practices": [],
    }
    for f in findings:
        key = f.category if f.category in by_category else "best_practices"
        by_category[key].append(f)

    def category_score(items: List[EvaluationFinding]) -> float:
        applicable = [
            STATUS_SCORE[i.status]
            for i in items
            if STATUS_SCORE.get(i.status) is not None
        ]
        if not applicable:
            return 70.0  # neutral when nothing applicable
        return round(sum(applicable) / len(applicable), 1)

    categories = CategoryScores(
        security=category_score(by_category["security"]),
        cost=category_score(by_category["cost"]),
        reliability=category_score(by_category["reliability"]),
        scalability=category_score(by_category["scalability"]),
        best_practices=category_score(by_category["best_practices"]),
    )
    overall = round(
        categories.security * weights["security"]
        + categories.cost * weights["cost"]
        + categories.reliability * weights["reliability"]
        + categories.scalability * weights["scalability"]
        + categories.best_practices * weights["best_practices"],
        1,
    )
    return ScoreReport(categories=categories, overall=overall, weights=weights)


class RulesEngine:
    """Runs all deterministic rule packs against an architecture."""

    def __init__(self) -> None:
        self.packs = [
            SecurityRules(),
            CostRules(),
            ReliabilityRules(),
            ScalabilityRules(),
            BestPracticeRules(),
        ]

    def evaluate(
        self,
        architecture: Architecture,
        requirements: Optional[Requirements] = None,
    ) -> List[EvaluationFinding]:
        findings: List[EvaluationFinding] = []
        for pack in self.packs:
            findings.extend(pack.evaluate(architecture, requirements))
        return findings

    def evaluate_and_score(
        self,
        architecture: Architecture,
        requirements: Optional[Requirements] = None,
    ) -> tuple[List[EvaluationFinding], ScoreReport]:
        findings = self.evaluate(architecture, requirements)
        return findings, score_findings(findings)
