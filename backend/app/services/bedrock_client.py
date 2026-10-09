"""Amazon Bedrock client with deterministic mock fallback."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from app.config import Settings, get_settings
from agent.architecture_planner import build_architecture_from_requirements
from app.models.schemas import (
    Architecture,
    EvaluationFinding,
    Requirements,
    RuleStatus,
)

logger = logging.getLogger(__name__)


class BedrockClient:
    """Wraps bedrock-runtime converse/invoke_model with demo fallback."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._client = None
        self.demo = self.settings.is_demo()
        if not self.demo:
            try:
                import boto3

                self._client = boto3.client(
                    "bedrock-runtime",
                    region_name=self.settings.effective_bedrock_region,
                )
            except Exception as exc:
                logger.warning("Bedrock client unavailable, using mock: %s", exc)
                self.demo = True
                self._client = None

    def _converse_json(self, system: str, user: str) -> Optional[dict]:
        if self.demo or self._client is None:
            return None
        try:
            response = self._client.converse(
                modelId=self.settings.bedrock_model_id,
                system=[{"text": system}],
                messages=[{"role": "user", "content": [{"text": user}]}],
                inferenceConfig={"maxTokens": 4096, "temperature": 0.2},
            )
            text = response["output"]["message"]["content"][0]["text"]
            # Extract JSON object from response
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                return json.loads(text[start : end + 1])
            start_a = text.find("[")
            end_a = text.rfind("]")
            if start_a >= 0 and end_a > start_a:
                return {"items": json.loads(text[start_a : end_a + 1])}
        except Exception as exc:
            logger.warning("Bedrock converse failed, falling back to mock: %s", exc)
        return None

    def generate_architecture(
        self,
        requirements: Dict[str, Any],
        clarification_answers: Optional[Dict[str, str]] = None,
    ) -> Architecture:
        system = (
            "You are InfraPilot AI. Design AWS architectures as JSON with "
            "nodes[{id,service_id,label,props}] and edges[{from,to,label}]. "
            "Never generate Terraform or CloudFormation. Never invent prices."
        )
        user = json.dumps(
            {
                "requirements": requirements,
                "clarification_answers": clarification_answers or {},
            }
        )
        data = self._converse_json(system, user)
        if data and "nodes" in data:
            try:
                return Architecture.model_validate(data)
            except Exception:
                pass
        req = Requirements.model_validate(requirements)
        return build_architecture_from_requirements(req)

    def analyze_gaps(
        self,
        architecture: Dict[str, Any],
        requirements: Dict[str, Any],
    ) -> List[EvaluationFinding]:
        system = (
            "Identify architecture gaps as JSON array of findings with "
            "rule_id, category, title, status (Pass|Fail|Warning|Unknown|Not Applicable), "
            "message, recommendation. Never mark Pass when evidence is missing — use Unknown."
        )
        user = json.dumps({"architecture": architecture, "requirements": requirements})
        data = self._converse_json(system, user)
        items = []
        if isinstance(data, dict):
            items = data.get("findings") or data.get("items") or []
        if not items:
            return self._mock_gap_findings(architecture, requirements)
        out: List[EvaluationFinding] = []
        for item in items:
            try:
                item.setdefault("source", "ai")
                out.append(EvaluationFinding.model_validate(item))
            except Exception:
                continue
        return out

    def optimize_architecture(
        self,
        architecture: Dict[str, Any],
        requirements: Dict[str, Any],
    ) -> Optional[dict]:
        # Return None to let OptimizationPlanner use deterministic logic
        system = (
            "Propose an optimized AWS architecture JSON with original, optimized, "
            "and changes. No Terraform/CloudFormation. No invented prices."
        )
        user = json.dumps({"architecture": architecture, "requirements": requirements})
        data = self._converse_json(system, user)
        return data

    def _mock_gap_findings(
        self,
        architecture: Dict[str, Any],
        requirements: Dict[str, Any],
    ) -> List[EvaluationFinding]:
        nodes = architecture.get("nodes") or []
        services = {n.get("service_id") for n in nodes}
        findings: List[EvaluationFinding] = []
        if "cloudwatch" not in services:
            findings.append(
                EvaluationFinding(
                    rule_id="MOCK-GAP-001",
                    category="reliability",
                    title="Observability evidence missing",
                    status=RuleStatus.UNKNOWN,
                    message=(
                        "No CloudWatch node — cannot confirm monitoring as Pass."
                    ),
                    recommendation="Add CloudWatch metrics and alarms.",
                    source="ai",
                )
            )
        workload = (requirements or {}).get("workload")
        if workload in ("web", "api") and "waf" not in services:
            findings.append(
                EvaluationFinding(
                    rule_id="MOCK-GAP-002",
                    category="security",
                    title="Edge protection gap",
                    status=RuleStatus.WARNING,
                    message="Web/API workload without WAF in the diagram.",
                    recommendation="Add AWS WAF at the edge.",
                    source="ai",
                )
            )
        return findings
