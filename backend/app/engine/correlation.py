"""Deterministic Correlation Rule Engine for APEX OSINT."""

from typing import List, Dict, Any, Set
from collections import defaultdict
from app.models.entity import Entity
from app.models.relationship import Relationship
from app.models.evidence import Evidence


class DeterministicCorrelator:
    """Computes evidence-backed correlations across discovered entities prior to AI reasoning."""

    @classmethod
    def evaluate_correlations(
        cls,
        entities: List[Entity],
        relationships: List[Relationship],
        evidence_list: List[Evidence]
    ) -> List[Dict[str, Any]]:
        """Evaluate deterministic rules to discover cross-entity connections."""
        new_correlations = []
        entity_by_norm = {e.normalized_value: e for e in entities}
        entity_by_id = {e.id: e for e in entities}

        # Existing edges set to avoid duplicates
        existing_edges: Set[tuple] = {
            (r.source_entity_id, r.target_entity_id, r.relation_type)
            for r in relationships
        }

        # Rule 1: Co-Hosting Correlation (Multiple domains resolving to same IP)
        ip_to_domains = defaultdict(list)
        for r in relationships:
            if r.relation_type == "RESOLVES_TO":
                src = entity_by_id.get(r.source_entity_id)
                tgt = entity_by_id.get(r.target_entity_id)
                if src and tgt and tgt.type == "IP":
                    ip_to_domains[tgt.id].append(src.id)

        for ip_id, domain_ids in ip_to_domains.items():
            if len(domain_ids) > 1:
                # Multiple domains share this IP
                for i in range(len(domain_ids)):
                    for j in range(i + 1, len(domain_ids)):
                        d1_id = domain_ids[i]
                        d2_id = domain_ids[j]
                        if (d1_id, d2_id, "HOSTED_ON") not in existing_edges:
                            new_correlations.append({
                                "source_entity_id": d1_id,
                                "target_entity_id": d2_id,
                                "relation_type": "ASSOCIATED_WITH",
                                "confidence": 0.85,
                                "reason": f"Both entities share co-hosted IP infrastructure.",
                                "is_ai_inferred": False,
                                "evidence_ids": [e.id for e in evidence_list if ip_id in (e.related_entity_ids_json or [])][:2]
                            })

        # Rule 2: Shared Domain Email Correlation
        # If an email's domain matches an investigated DOMAIN entity, link them
        for ent in entities:
            if ent.type == "EMAIL" and "@" in ent.value:
                domain_part = ent.value.split("@")[1].lower()
                domain_ent = entity_by_norm.get(domain_part)
                if domain_ent and (ent.id, domain_ent.id, "ASSOCIATED_WITH") not in existing_edges:
                    new_correlations.append({
                        "source_entity_id": ent.id,
                        "target_entity_id": domain_ent.id,
                        "relation_type": "ASSOCIATED_WITH",
                        "confidence": 0.98,
                        "reason": f"Email address belongs to domain '{domain_part}'.",
                        "is_ai_inferred": False,
                        "evidence_ids": []
                    })

        # Rule 3: Repository Contributor to Organization / Domain Correlation
        for ent in entities:
            if ent.type == "REPOSITORY" and "/" in ent.value:
                owner_part = ent.value.split("/")[0].lower()
                owner_ent = entity_by_norm.get(owner_part)
                if owner_ent and (owner_ent.id, ent.id, "OWNS") not in existing_edges:
                    new_correlations.append({
                        "source_entity_id": owner_ent.id,
                        "target_entity_id": ent.id,
                        "relation_type": "OWNS",
                        "confidence": 0.95,
                        "reason": f"Entity is designated owner of repository '{ent.value}'.",
                        "is_ai_inferred": False,
                        "evidence_ids": []
                    })

        return new_correlations
