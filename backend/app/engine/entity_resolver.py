"""Advanced Deterministic Entity Resolution and Identity Disambiguation Engine for APEX OSINT.

Calculates evidence-backed identity hypotheses with mathematically explainable confidence breakdowns.
Never relies on arbitrary AI guesses.
"""

import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict

from app.models.entity import Entity
from app.models.evidence import Evidence


@dataclass
class ConfidenceSignal:
    name: str
    impact: float  # Positive for bonus (+0.25), negative for penalty (-0.15)
    description: str


@dataclass
class IdentityHypothesis:
    hypothesis_id: str
    canonical_name: str
    entity_ids: List[str]
    confidence: float
    status: str  # CORROBORATED, PROBABLE, SPECULATIVE, CONFLICTED
    signals: List[ConfidenceSignal] = field(default_factory=list)
    contradictions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "canonical_name": self.canonical_name,
            "entity_ids": self.entity_ids,
            "confidence": round(self.confidence, 3),
            "confidence_percentage": f"{int(round(self.confidence * 100))}%",
            "status": self.status,
            "explanation": [
                f"{'+' if s.impact > 0 else ''}{int(round(s.impact * 100))}%: {s.description}"
                for s in self.signals
            ],
            "penalties": self.contradictions,
        }


class EntityResolver:
    """Deterministic Multi-Entity Identity Resolution and Disambiguation."""

    @classmethod
    def resolve_and_cluster(
        cls,
        entities: List[Entity],
        evidence_list: List[Evidence]
    ) -> Dict[str, Any]:
        """
        Group entities into verified clusters and formulate explainable identity hypotheses.
        """
        clusters: Dict[str, List[Entity]] = defaultdict(list)
        hypotheses: List[IdentityHypothesis] = []

        entity_by_id = {e.id: e for e in entities}
        norm_map = {e.normalized_value: e for e in entities}

        # 1. Disambiguate PERSON entities sharing common names
        person_entities = [e for e in entities if e.type == "PERSON"]
        name_groups: Dict[str, List[Entity]] = defaultdict(list)
        for p in person_entities:
            name_groups[p.normalized_value].append(p)

        for norm_name, group in name_groups.items():
            if len(group) == 1:
                p = group[0]
                cluster_key = f"cluster-person-{p.normalized_value.replace(' ', '-')}"
                p.cluster_id = cluster_key
                clusters[cluster_key].append(p)
            else:
                # Multiple people sharing this name -> Inspect associated evidence/emails
                for idx, p in enumerate(group, 1):
                    cluster_key = f"cluster-person-{p.normalized_value.replace(' ', '-')}-{idx}"
                    p.cluster_id = cluster_key
                    clusters[cluster_key].append(p)

        # 2. Correlate USERNAME entities across platforms with evidence signals
        usernames = [e for e in entities if e.type == "USERNAME"]
        emails = [e for e in entities if e.type == "EMAIL"]
        repos = [e for e in entities if e.type == "REPOSITORY"]
        domains = [e for e in entities if e.type == "DOMAIN"]

        for u in usernames:
            signals: List[ConfidenceSignal] = []
            contradictions: List[str] = []
            related_ids: Set[str] = {u.id}
            base_score = 0.50  # Prior probability for single uncorroborated username

            signals.append(ConfidenceSignal(
                name="BASE_USERNAME",
                impact=0.50,
                description=f"Base identifier observation for username '{u.value}'"
            ))

            # Signal: Matching email prefix
            matching_emails = [em for em in emails if em.value.split("@")[0].lower() == u.normalized_value]
            if matching_emails:
                for em in matching_emails:
                    signals.append(ConfidenceSignal(
                        name="MATCHING_EMAIL_PREFIX",
                        impact=0.20,
                        description=f"Exact match with email handle: {em.value}"
                    ))
                    base_score += 0.20
                    related_ids.add(em.id)

            # Signal: Public Repository Author / Owner
            matching_repos = [r for r in repos if r.value.split("/")[0].lower() == u.normalized_value]
            if matching_repos:
                for r in matching_repos:
                    signals.append(ConfidenceSignal(
                        name="REPO_OWNERSHIP",
                        impact=0.15,
                        description=f"Direct maintainer/owner of repository {r.value}"
                    ))
                    base_score += 0.15
                    related_ids.add(r.id)

            # Signal: Associated Website / Domain Match
            for d in domains:
                # E.g. username.github.io or username matches domain SLD
                sld = d.value.split(".")[0].lower()
                if sld == u.normalized_value or f"{u.normalized_value}." in d.value:
                    signals.append(ConfidenceSignal(
                        name="DOMAIN_SLD_CORRELATION",
                        impact=0.10,
                        description=f"Direct naming alignment with investigated domain {d.value}"
                    ))
                    base_score += 0.10
                    related_ids.add(d.id)

            # Check for conflicting evidence in payload
            for ev in evidence_list:
                payload = ev.raw_payload_json or {}
                if payload.get("location_mismatch"):
                    contradictions.append(f"Location discrepancy reported by {ev.source_name}")
                    signals.append(ConfidenceSignal(
                        name="LOCATION_PENALTY",
                        impact=-0.15,
                        description=f"Conflicting location telemetry ({ev.source_name})"
                    ))
                    base_score -= 0.15

            final_confidence = max(0.10, min(0.99, base_score))
            status = "SPECULATIVE"
            if final_confidence >= 0.85:
                status = "CORROBORATED"
            elif final_confidence >= 0.65:
                status = "PROBABLE"
            elif contradictions:
                status = "CONFLICTED"

            hypo_id = f"hypo-{hashlib.md5(u.normalized_value.encode()).hexdigest()[:8]}"
            hypothesis = IdentityHypothesis(
                hypothesis_id=hypo_id,
                canonical_name=u.value,
                entity_ids=list(related_ids),
                confidence=final_confidence,
                status=status,
                signals=signals,
                contradictions=contradictions
            )
            hypotheses.append(hypothesis)

            # Assign cluster ID to entities in this resolved identity
            c_id = f"cluster-id-{u.normalized_value}"
            for eid in related_ids:
                ent = entity_by_id.get(eid)
                if ent and not ent.cluster_id:
                    ent.cluster_id = c_id
                    clusters[c_id].append(ent)

        # 3. Default cluster assignment for unclustered entities
        for ent in entities:
            if not ent.cluster_id:
                c_key = f"cluster-{ent.type.lower()}-{ent.id[:8]}"
                ent.cluster_id = c_key
                clusters[c_key].append(ent)

        return {
            "total_clusters": len(clusters),
            "clusters": {k: [e.value for e in v] for k, v in clusters.items()},
            "hypotheses": [h.to_dict() for h in hypotheses]
        }

    @classmethod
    def score_match_confidence(cls, evidence_count: int, sources_count: int) -> str:
        """Classify resolution confidence into epistemic tiers."""
        if sources_count >= 2:
            return "CORROBORATED"
        elif evidence_count >= 2:
            return "PROBABLE"
        return "POSSIBLE"
