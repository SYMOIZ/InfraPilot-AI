"""Scoring unit tests."""

from __future__ import annotations

from app.models.schemas import EvaluationFinding, RuleStatus
from rules.engine import score_findings


def test_score_all_pass():
    findings = [
        EvaluationFinding(
            rule_id="a",
            category="security",
            title="t",
            status=RuleStatus.PASS,
            message="ok",
        ),
        EvaluationFinding(
            rule_id="b",
            category="cost",
            title="t",
            status=RuleStatus.PASS,
            message="ok",
        ),
        EvaluationFinding(
            rule_id="c",
            category="reliability",
            title="t",
            status=RuleStatus.PASS,
            message="ok",
        ),
        EvaluationFinding(
            rule_id="d",
            category="scalability",
            title="t",
            status=RuleStatus.PASS,
            message="ok",
        ),
        EvaluationFinding(
            rule_id="e",
            category="best_practices",
            title="t",
            status=RuleStatus.PASS,
            message="ok",
        ),
    ]
    report = score_findings(findings)
    assert report.categories.security == 100.0
    assert report.overall == 100.0


def test_score_fail_lowers_category():
    findings = [
        EvaluationFinding(
            rule_id="a",
            category="security",
            title="t",
            status=RuleStatus.FAIL,
            message="bad",
        ),
        EvaluationFinding(
            rule_id="b",
            category="security",
            title="t",
            status=RuleStatus.PASS,
            message="ok",
        ),
    ]
    report = score_findings(findings)
    assert report.categories.security == 50.0


def test_not_applicable_excluded():
    findings = [
        EvaluationFinding(
            rule_id="a",
            category="cost",
            title="t",
            status=RuleStatus.NOT_APPLICABLE,
            message="n/a",
        ),
        EvaluationFinding(
            rule_id="b",
            category="cost",
            title="t",
            status=RuleStatus.PASS,
            message="ok",
        ),
    ]
    report = score_findings(findings)
    assert report.categories.cost == 100.0


def test_unknown_scores_mid():
    findings = [
        EvaluationFinding(
            rule_id="a",
            category="security",
            title="t",
            status=RuleStatus.UNKNOWN,
            message="?",
        )
    ]
    report = score_findings(findings)
    assert report.categories.security == 50.0


def test_sample_architecture_scores(sample_architecture, sample_requirements):
    from rules.engine import RulesEngine

    findings, scores = RulesEngine().evaluate_and_score(
        sample_architecture, sample_requirements
    )
    assert 0 <= scores.overall <= 100
    assert scores.categories.security >= 0
    assert findings
