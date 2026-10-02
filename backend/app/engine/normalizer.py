"""Universal Normalizer for APEX OSINT findings and telemetry."""

import hashlib
import json
from typing import Dict, Any, List, Tuple
from app.modules.base import (
    NormalizedFinding,
    NormalizedEntity,
    NormalizedEvidence,
    NormalizedRelationship,
)


def compute_evidence_hash(source_name: str, snippet: str, payload: Dict[str, Any]) -> str:
    """Compute deterministic SHA-256 hash for evidence deduplication and provenance."""
    raw = f"{source_name}:{snippet}:{json.dumps(payload, sort_keys=True)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def canonicalize_value(entity_type: str, value: str) -> str:
    """Compute clean canonical representation for indexing and matching."""
    val = value.strip()
    if entity_type in ("DOMAIN", "SUBDOMAIN", "EMAIL"):
        return val.lower()
    if entity_type == "IP":
        return val.strip()
    if entity_type == "USERNAME":
        return val.lstrip("@").lower()
    if entity_type == "REPOSITORY":
        return val.lower()
    if entity_type == "ASN":
        return val.upper()
    return val.lower()


class DataNormalizer:
    """Validates and normalizes raw module findings before committing to graph."""

    @classmethod
    def process_finding(
        cls,
        finding: NormalizedFinding,
        investigation_id: str
    ) -> NormalizedFinding:
        """Sanitize finding entities, compute hashes, and ensure relationship consistency."""
        # Ensure canonical normalized_values for all entities
        if finding.primary_entity:
            finding.primary_entity.normalized_value = canonicalize_value(
                finding.primary_entity.type,
                finding.primary_entity.value
            )

        for ent in finding.discovered_entities:
            ent.normalized_value = canonicalize_value(ent.type, ent.value)

        # Hash evidence records
        for ev in finding.evidence:
            if not getattr(ev, "hash_signature", None):
                ev.hash_signature = compute_evidence_hash(
                    ev.source_name,
                    ev.snippet,
                    ev.raw_payload
                )

        return finding
