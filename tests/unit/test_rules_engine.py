"""Rules engine unit tests."""

from __future__ import annotations

from app.models.schemas import (
    Architecture,
    ArchitectureNode,
    AvailabilityTarget,
    DataSensitivity,
    Requirements,
    RuleStatus,
    WorkloadType,
)
from rules.engine import RulesEngine


def test_public_s3_without_encryption_fails():
    arch = Architecture(
        nodes=[
            ArchitectureNode(
                id="s3",
                service_id="s3",
                label="Public Bucket",
                props={"public": True, "encryption": False},
            ),
            ArchitectureNode(
                id="iam",
                service_id="iam",
                label="IAM",
                props={"wildcard_actions": False},
            ),
            ArchitectureNode(id="cw", service_id="cloudwatch", label="CW", props={}),
        ]
    )
    findings = RulesEngine().evaluate(arch)
    statuses = {(f.rule_id, f.status) for f in findings}
    assert ("SEC-S3-001", RuleStatus.FAIL) in statuses or any(
        f.rule_id == "SEC-S3-002" and f.status == RuleStatus.FAIL for f in findings
    )


def test_iam_wildcard_fails():
    arch = Architecture(
        nodes=[
            ArchitectureNode(
                id="iam",
                service_id="iam",
                label="Open IAM",
                props={"wildcard_actions": True},
            )
        ]
    )
    findings = RulesEngine().evaluate(arch)
    assert any(
        f.rule_id == "SEC-IAM-001" and f.status == RuleStatus.FAIL for f in findings
    )


def test_missing_cloudwatch_warning():
    arch = Architecture(
        nodes=[ArchitectureNode(id="l", service_id="lambda", label="Fn", props={})]
    )
    findings = RulesEngine().evaluate(arch)
    assert any(
        f.rule_id == "REL-MON-001" and f.status == RuleStatus.WARNING for f in findings
    )


def test_missing_evidence_is_unknown_not_pass():
    arch = Architecture(
        nodes=[
            ArchitectureNode(id="s3", service_id="s3", label="Bucket", props={}),
            ArchitectureNode(id="iam", service_id="iam", label="IAM", props={}),
        ]
    )
    findings = RulesEngine().evaluate(arch)
    s3 = [f for f in findings if f.rule_id == "SEC-S3-001"]
    assert s3
    assert s3[0].status == RuleStatus.UNKNOWN


def test_multi_az_for_critical_ha():
    req = Requirements(
        purpose="HA app",
        availability=AvailabilityTarget.CRITICAL,
        workload=WorkloadType.WEB,
    )
    arch = Architecture(
        nodes=[
            ArchitectureNode(
                id="rds",
                service_id="rds",
                label="DB",
                props={"multi_az": False},
            ),
            ArchitectureNode(id="cw", service_id="cloudwatch", label="CW", props={}),
        ]
    )
    findings = RulesEngine().evaluate(arch, req)
    assert any(
        f.rule_id == "REL-AZ-001" and f.status == RuleStatus.FAIL for f in findings
    )


def test_kms_required_for_regulated():
    req = Requirements(
        purpose="Regulated app",
        data_sensitivity=DataSensitivity.REGULATED,
        workload=WorkloadType.API,
    )
    arch = Architecture(
        nodes=[
            ArchitectureNode(id="l", service_id="lambda", label="Fn", props={}),
            ArchitectureNode(id="cw", service_id="cloudwatch", label="CW", props={}),
        ]
    )
    findings = RulesEngine().evaluate(arch, req)
    assert any(
        f.rule_id == "SEC-KMS-001" and f.status == RuleStatus.FAIL for f in findings
    )


def test_sample_architecture_has_passes(sample_architecture, sample_requirements):
    findings = RulesEngine().evaluate(sample_architecture, sample_requirements)
    assert any(f.status == RuleStatus.PASS for f in findings)
    assert findings  # deterministic non-empty
