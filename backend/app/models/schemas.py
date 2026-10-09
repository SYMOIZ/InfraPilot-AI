"""Pydantic schemas for InfraPilot AI."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid4())


class RuleStatus(str, Enum):
    PASS = "Pass"
    FAIL = "Fail"
    WARNING = "Warning"
    UNKNOWN = "Unknown"
    NOT_APPLICABLE = "Not Applicable"


class WorkloadType(str, Enum):
    WEB = "web"
    API = "api"
    BATCH = "batch"
    STREAMING = "streaming"
    DATA = "data"
    OTHER = "other"


class DataSensitivity(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    REGULATED = "regulated"


class AvailabilityTarget(str, Enum):
    STANDARD = "standard"
    HIGH = "high"
    CRITICAL = "critical"


class Requirements(BaseModel):
    """Customer workload requirements."""

    purpose: str = Field(..., description="What the system should accomplish")
    workload: WorkloadType = WorkloadType.WEB
    traffic: str = Field(
        default="low",
        description="Expected traffic pattern, e.g. low/medium/high or RPS",
    )
    data_sensitivity: DataSensitivity = DataSensitivity.INTERNAL
    availability: AvailabilityTarget = AvailabilityTarget.STANDARD
    recovery: str = Field(
        default="best-effort",
        description="RTO/RPO style recovery expectations",
    )
    budget: str = Field(
        default="moderate",
        description="Qualitative budget: low/moderate/high — never invent prices",
    )
    region: str = "us-east-1"
    scalability: str = Field(
        default="moderate",
        description="Expected scale needs",
    )
    constraints: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class ArchitectureNode(BaseModel):
    """A service node in an architecture diagram."""

    id: str
    service_id: str = Field(..., description="Catalog service identifier")
    label: str
    props: Dict[str, Any] = Field(default_factory=dict)
    x: Optional[float] = None
    y: Optional[float] = None


class ArchitectureEdge(BaseModel):
    """Directed connection between architecture nodes."""

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    id: Optional[str] = None
    from_node: str = Field(..., alias="from", serialization_alias="from")
    to_node: str = Field(..., alias="to", serialization_alias="to")
    label: Optional[str] = None


class Architecture(BaseModel):
    """Architecture graph: nodes + edges."""

    id: str = Field(default_factory=_new_id)
    name: str = "Untitled Architecture"
    nodes: List[ArchitectureNode] = Field(default_factory=list)
    edges: List[ArchitectureEdge] = Field(default_factory=list)
    confirmed: bool = False
    source: str = Field(
        default="generated",
        description="generated | uploaded | optimized | sample",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvaluationFinding(BaseModel):
    """Single rule or AI gap finding."""

    id: str = Field(default_factory=_new_id)
    rule_id: str
    category: str
    title: str
    status: RuleStatus
    severity: str = "medium"
    message: str
    evidence: Optional[str] = None
    recommendation: Optional[str] = None
    source: str = "rules"  # rules | ai


class CategoryScores(BaseModel):
    security: float = 0.0
    cost: float = 0.0
    reliability: float = 0.0
    scalability: float = 0.0
    best_practices: float = 0.0


class ScoreReport(BaseModel):
    categories: CategoryScores
    overall: float
    weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "security": 0.30,
            "cost": 0.15,
            "reliability": 0.25,
            "scalability": 0.15,
            "best_practices": 0.15,
        }
    )


class EvaluationReport(BaseModel):
    project_id: str
    findings: List[EvaluationFinding] = Field(default_factory=list)
    scores: ScoreReport
    summary: str = ""
    gaps: List[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=_utcnow)


class OptimizationChange(BaseModel):
    change_type: str  # add | remove | modify | replace
    service_id: Optional[str] = None
    description: str
    rationale: str
    impact_categories: List[str] = Field(default_factory=list)


class OptimizationProposal(BaseModel):
    project_id: str
    original: Architecture
    optimized: Architecture
    changes: List[OptimizationChange] = Field(default_factory=list)
    summary: str = ""
    cost_notes: str = Field(
        default="Qualitative cost guidance only — no invented AWS list prices.",
    )
    created_at: datetime = Field(default_factory=_utcnow)


class CompareResponse(BaseModel):
    project_id: str
    original: Optional[Architecture] = None
    optimized: Optional[Architecture] = None
    changes: List[OptimizationChange] = Field(default_factory=list)
    original_scores: Optional[ScoreReport] = None
    optimized_scores: Optional[ScoreReport] = None


class ProjectCreate(BaseModel):
    name: str = "New Project"
    description: Optional[str] = None


class ProjectSummary(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    has_requirements: bool = False
    has_architecture: bool = False
    has_evaluation: bool = False
    has_optimization: bool = False


class Project(BaseModel):
    id: str = Field(default_factory=_new_id)
    name: str = "New Project"
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    requirements: Optional[Requirements] = None
    architecture: Optional[Architecture] = None
    optimized_architecture: Optional[Architecture] = None
    evaluation: Optional[EvaluationReport] = None
    optimization: Optional[OptimizationProposal] = None
    uploaded_files: List[str] = Field(default_factory=list)
    clarification_answers: Dict[str, str] = Field(default_factory=dict)

    def touch(self) -> None:
        self.updated_at = _utcnow()

    def summary(self) -> ProjectSummary:
        return ProjectSummary(
            id=self.id,
            name=self.name,
            description=self.description,
            created_at=self.created_at,
            updated_at=self.updated_at,
            has_requirements=self.requirements is not None,
            has_architecture=self.architecture is not None,
            has_evaluation=self.evaluation is not None,
            has_optimization=self.optimization is not None,
        )


class ClarificationRequest(BaseModel):
    answers: Dict[str, str] = Field(default_factory=dict)


class ClarificationQuestion(BaseModel):
    id: str
    question: str
    reason: str


class ClarificationResponse(BaseModel):
    project_id: str
    questions: List[ClarificationQuestion] = Field(default_factory=list)
    message: str = ""


class ConfirmArchitectureRequest(BaseModel):
    architecture: Architecture
    confirmed: bool = True


class GenerateRequest(BaseModel):
    regenerate: bool = False
    prompt: Optional[str] = None


class ReportResponse(BaseModel):
    project_id: str
    title: str
    executive_summary: str
    requirements: Optional[Requirements] = None
    architecture: Optional[Architecture] = None
    evaluation: Optional[EvaluationReport] = None
    optimization: Optional[OptimizationProposal] = None
    generated_at: datetime = Field(default_factory=_utcnow)
