"""Interpret and clarify customer requirements."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.models.schemas import (
    ClarificationQuestion,
    Requirements,
)


class RequirementsInterpreter:
    """Produces clarification questions and normalizes requirement text."""

    AMBIGUOUS_TRAFFIC = {"unknown", "tbd", "?", ""}
    AMBIGUOUS_BUDGET = {"unknown", "tbd", "?", ""}

    def clarify(
        self,
        requirements: Optional[Requirements],
        existing_answers: Optional[Dict[str, str]] = None,
    ) -> List[ClarificationQuestion]:
        existing_answers = existing_answers or {}
        questions: List[ClarificationQuestion] = []

        if requirements is None:
            return [
                ClarificationQuestion(
                    id="purpose",
                    question="What is the primary purpose of this system?",
                    reason="Requirements have not been provided yet.",
                ),
                ClarificationQuestion(
                    id="workload",
                    question="Is this primarily a web app, API, batch, or streaming workload?",
                    reason="Workload type drives architecture patterns.",
                ),
                ClarificationQuestion(
                    id="data_sensitivity",
                    question="What is the data sensitivity (public/internal/confidential/regulated)?",
                    reason="Sensitivity drives encryption and compliance controls.",
                ),
            ]

        if requirements.traffic.lower() in self.AMBIGUOUS_TRAFFIC and "traffic" not in existing_answers:
            questions.append(
                ClarificationQuestion(
                    id="traffic",
                    question="What peak traffic or RPS do you expect?",
                    reason="Traffic drives scaling and edge design.",
                )
            )

        if requirements.budget.lower() in self.AMBIGUOUS_BUDGET and "budget" not in existing_answers:
            questions.append(
                ClarificationQuestion(
                    id="budget",
                    question="Is the budget constrained (low), moderate, or flexible (high)?",
                    reason="Budget guides serverless vs container/DB choices (qualitative).",
                )
            )

        if (
            requirements.availability.value == "critical"
            and "recovery" not in existing_answers
            and requirements.recovery in ("best-effort", "")
        ):
            questions.append(
                ClarificationQuestion(
                    id="recovery",
                    question="What RTO/RPO targets do you need for critical availability?",
                    reason="Critical availability needs explicit recovery targets.",
                )
            )

        if (
            requirements.data_sensitivity.value == "regulated"
            and "compliance" not in existing_answers
        ):
            questions.append(
                ClarificationQuestion(
                    id="compliance",
                    question="Which compliance regimes apply (e.g. HIPAA, PCI, GDPR)?",
                    reason="Regulated data may require additional controls.",
                )
            )

        if not requirements.constraints and "constraints" not in existing_answers:
            questions.append(
                ClarificationQuestion(
                    id="constraints",
                    question="Any hard constraints (regions, prohibited services, vendor lock-in)?",
                    reason="Constraints prevent invalid architecture proposals.",
                )
            )

        return questions

    def apply_answers(
        self,
        requirements: Requirements,
        answers: Dict[str, str],
    ) -> Requirements:
        data = requirements.model_dump()
        if "traffic" in answers:
            data["traffic"] = answers["traffic"]
        if "budget" in answers:
            data["budget"] = answers["budget"]
        if "recovery" in answers:
            data["recovery"] = answers["recovery"]
        if "constraints" in answers:
            raw = answers["constraints"]
            data["constraints"] = [c.strip() for c in raw.split(",") if c.strip()]
        if "compliance" in answers:
            notes = data.get("notes") or ""
            data["notes"] = f"{notes}\nCompliance: {answers['compliance']}".strip()
        return Requirements(**data)

    def to_prompt_context(self, requirements: Requirements) -> Dict[str, Any]:
        return requirements.model_dump()
