"""Base OSINT Module plugin specification and data normalization contracts."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional


@dataclass
class NormalizedEntity:
    type: str  # PERSON, ORGANIZATION, DOMAIN, SUBDOMAIN, IP, ASN, EMAIL, USERNAME, URL, REPOSITORY, DOCUMENT, etc.
    value: str
    normalized_value: str
    confidence: float = 1.0
    cluster_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedEvidence:
    source_name: str
    source_type: str
    source_url: Optional[str]
    snippet: str
    collection_method: str = "DIRECT_QUERY"
    confidence: float = 1.0
    epistemic_label: str = "OBSERVED"  # OBSERVED, CORROBORATED, AI_INFERENCE, UNVERIFIED
    raw_payload: Dict[str, Any] = field(default_factory=dict)
    related_entity_values: List[str] = field(default_factory=list)


@dataclass
class NormalizedRelationship:
    source_value: str
    source_type: str
    target_value: str
    target_type: str
    relation_type: str  # OWNS, MENTIONS, HOSTED_ON, RESOLVES_TO, AUTHORED, CONTRIBUTES_TO, LINKS_TO, ASSOCIATED_WITH, DISCOVERED_FROM, CERTIFICATE_FOR, SUBDOMAIN_OF
    confidence: float = 1.0
    is_ai_inferred: bool = False
    evidence_indices: List[int] = field(default_factory=list)  # indices into NormalizedFinding.evidence


@dataclass
class NormalizedTimelineEvent:
    timestamp: datetime
    event_type: str
    title: str
    description: str
    entity_value: Optional[str] = None
    confidence: float = 1.0


@dataclass
class NormalizedFinding:
    primary_entity: Optional[NormalizedEntity] = None
    discovered_entities: List[NormalizedEntity] = field(default_factory=list)
    relationships: List[NormalizedRelationship] = field(default_factory=list)
    evidence: List[NormalizedEvidence] = field(default_factory=list)
    timeline_events: List[NormalizedTimelineEvent] = field(default_factory=list)
    raw_observations: List[Dict[str, Any]] = field(default_factory=list)

    def add_entity(
        self,
        type: str,
        value: str,
        confidence: float = 1.0,
        normalized_value: Optional[str] = None,
        provenance: str = "OBSERVED",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> NormalizedEntity:
        norm = normalized_value or value.lower().strip()
        ent = NormalizedEntity(
            type=type.upper().strip(),
            value=value,
            normalized_value=norm,
            confidence=confidence,
            metadata=metadata or {},
        )
        self.discovered_entities.append(ent)
        return ent

    def add_evidence(
        self,
        source_name: str,
        source_type: str,
        snippet: str,
        source_url: Optional[str] = None,
        collection_method: str = "DIRECT_QUERY",
        confidence: float = 1.0,
        epistemic_label: str = "OBSERVED",
        raw_payload: Optional[Dict[str, Any]] = None,
        related_entity_values: Optional[List[str]] = None,
    ) -> NormalizedEvidence:
        ev = NormalizedEvidence(
            source_name=source_name,
            source_type=source_type,
            source_url=source_url,
            snippet=snippet,
            collection_method=collection_method,
            confidence=confidence,
            epistemic_label=epistemic_label,
            raw_payload=raw_payload or {},
            related_entity_values=related_entity_values or [],
        )
        self.evidence.append(ev)
        return ev

    def add_relationship(
        self,
        source_type: str,
        source_value: str,
        target_type: str,
        target_value: str,
        relation_type: str = "ASSOCIATED_WITH",
        confidence: float = 1.0,
        is_ai_inferred: bool = False,
        evidence_indices: Optional[List[int]] = None,
    ) -> NormalizedRelationship:
        rel = NormalizedRelationship(
            source_value=source_value,
            source_type=source_type.upper().strip(),
            target_value=target_value,
            target_type=target_type.upper().strip(),
            relation_type=relation_type,
            confidence=confidence,
            is_ai_inferred=is_ai_inferred,
            evidence_indices=evidence_indices or [],
        )
        self.relationships.append(rel)
        return rel


@dataclass
class ModuleHealth:
    name: str
    status: str  # HEALTHY, DEGRADED, DISABLED, REQUIRES_KEY
    average_latency_ms: float = 0.0
    error_rate: float = 0.0
    last_run: Optional[datetime] = None
    message: Optional[str] = None


class BaseOSINTModule(ABC):
    """Abstract base class for all APEX OSINT intelligence collectors."""

    name: str = "base_module"
    display_name: str = "Base Module"
    description: str = "Base OSINT Collector"
    category: str = "GENERAL"  # DOMAIN, NETWORK, USERNAME, EMAIL, GITHUB, WEB, DOCUMENT, PHONE
    target_types: List[str] = []
    requirements: List[str] = []
    rate_limit: float = 2.0  # requests per second
    source: str = "Public"
    license: str = "Open Source"
    enabled: bool = True
    safety_level: str = "SAFE_PUBLIC"

    def can_handle(self, target_type: str, target_value: str) -> bool:
        """Return True if this module can collect intelligence for the specified target type."""
        if not self.enabled:
            return False
        t = target_type.upper().strip()
        if t in [x.upper().strip() for x in self.target_types]:
            return True
        # Canonical aliases mapping
        aliases = {
            "PHONE_NUMBER": ["PHONE", "PHONE_NUMBER", "TELEPHONE"],
            "PHONE": ["PHONE", "PHONE_NUMBER", "TELEPHONE"],
            "PERSON_NAME": ["PERSON", "PERSON_NAME"],
            "PERSON": ["PERSON", "PERSON_NAME"],
            "ORGANIZATION_NAME": ["ORGANIZATION", "ORGANIZATION_NAME"],
            "ORGANIZATION": ["ORGANIZATION", "ORGANIZATION_NAME"],
            "SUBDOMAIN": ["DOMAIN", "SUBDOMAIN"],
            "DOMAIN": ["DOMAIN", "SUBDOMAIN"],
            "GITHUB_USER": ["USERNAME", "PERSON"],
            "GITHUB_REPO": ["REPOSITORY"],
            "BITCOIN_ADDRESS": ["CRYPTO_ADDRESS", "BITCOIN_ADDRESS"],
            "CRYPTO_ADDRESS": ["BITCOIN_ADDRESS", "CRYPTO_ADDRESS"],
            "URL": ["DOMAIN", "URL"],
        }
        for alias in aliases.get(t, []):
            if alias in [x.upper().strip() for x in self.target_types]:
                return True
        return False

    @abstractmethod
    async def collect(self, target_value: str, target_type: str, context: Dict[str, Any]) -> NormalizedFinding:
        """Execute the collection logic and return a strictly normalized finding with evidence."""
        pass

    async def health_check(self) -> ModuleHealth:
        """Perform a quick health and connectivity check."""
        return ModuleHealth(
            name=self.name,
            status="HEALTHY" if self.enabled else "DISABLED",
            message="Ready"
        )

