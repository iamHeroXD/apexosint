"""Pydantic schemas for APEX OSINT API."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class WorkspaceOut(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: datetime
    investigations_count: int = 0


class UniversalQueryRequest(BaseModel):
    query: str = Field(..., description="Universal target input (any entity or comma-separated list)")


class TargetHypothesisOut(BaseModel):
    type: str
    confidence: float
    percentage: int
    explanation: str
    recommended_modules: List[str]


class AnalyzedTargetOut(BaseModel):
    raw_input: str
    normalized_value: str
    primary_type: str
    primary_confidence: float
    hypotheses: List[TargetHypothesisOut]
    planned_investigation: List[str]
    extraction_metadata: Dict[str, Any] = Field(default_factory=dict)


class InvestigationCreate(BaseModel):
    workspace_id: str
    title: str = Field(..., min_length=1, max_length=256)
    target_query: str = Field(..., description="Universal target input")
    mode: str = Field(default="standard", description="quick, standard, deep, custom")
    depth: int = Field(default=1, ge=0, le=3)
    is_demo: bool = False


class InvestigationOut(BaseModel):
    id: str
    workspace_id: str
    title: str
    status: str
    mode: str
    depth: int
    is_demo: bool
    summary_json: Optional[Dict[str, Any]]
    created_at: datetime


class EntityOut(BaseModel):
    id: str
    type: str
    value: str
    normalized_value: str
    cluster_id: Optional[str]
    confidence: float
    provenance_label: str
    is_bookmarked: bool
    first_seen: datetime
    metadata_json: Optional[Dict[str, Any]]


class EvidenceOut(BaseModel):
    id: str
    source_name: str
    source_type: str
    source_url: Optional[str]
    collection_method: str
    confidence: float
    epistemic_label: str
    snippet: str
    raw_payload_json: Optional[Dict[str, Any]]
    related_entity_ids_json: Optional[List[str]]
    collected_at: datetime
    is_bookmarked: bool


class RelationshipOut(BaseModel):
    id: str
    source_entity_id: str
    target_entity_id: str
    relation_type: str
    confidence: float
    is_ai_inferred: bool
    evidence_ids_json: Optional[List[str]]


class TimelineEventOut(BaseModel):
    id: str
    timestamp: datetime
    event_type: str
    title: str
    description: str
    confidence: float
    entity_id: Optional[str]
    evidence_id: Optional[str]


class ContradictionOut(BaseModel):
    id: str
    attribute_name: str
    source_a_name: str
    source_a_claim: str
    source_b_name: str
    source_b_claim: str
    explanation: str
    resolved: bool


class AIChatRequest(BaseModel):
    investigation_id: str
    message: str
    mode: str = Field(default="ANALYST")


class AIChatResponse(BaseModel):
    response: str
    cited_evidence_ids: List[str] = Field(default_factory=list)
    confidence: float = 0.90
    classification: str = "AI INFERENCE"
    tool_executed: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_result: Optional[Dict[str, Any]] = None


class ReportCreate(BaseModel):
    format: str = Field(default="markdown")  # markdown, html, json
    classification: str = Field(default="CONFIDENTIAL / DEFENSIVE OSINT REPORT")
