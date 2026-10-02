"""Contradiction & Divergent Fact Detection Engine for APEX OSINT."""

from typing import List, Dict, Any, Optional
from app.models.evidence import Evidence
from app.models.entity import Entity


class ContradictionDetector:
    """Identifies contradictory or irreconcilable claims between independent evidence sources."""

    @classmethod
    def scan_for_contradictions(
        cls,
        entities: List[Entity],
        evidence_list: List[Evidence]
    ) -> List[Dict[str, Any]]:
        """Compare attributes across collected evidence for each entity to detect discrepancies."""
        contradictions = []

        # Analyze evidence clustered by entity
        entity_evidence_map: Dict[str, List[Evidence]] = {}
        for ev in evidence_list:
            related_ids = ev.related_entity_ids_json or []
            for eid in related_ids:
                if eid not in entity_evidence_map:
                    entity_evidence_map[eid] = []
                entity_evidence_map[eid].append(ev)

        for ent in entities:
            evs = entity_evidence_map.get(ent.id, [])
            if len(evs) < 2:
                continue

            # Compare foundation year / dates claims if present in payload
            dates_seen = []
            for ev in evs:
                payload = ev.raw_payload_json or {}
                if "registered_year" in payload:
                    dates_seen.append((ev, "registered_year", str(payload["registered_year"])))
                elif "founded_claim" in payload:
                    dates_seen.append((ev, "founded_claim", str(payload["founded_claim"])))

            if len(dates_seen) >= 2:
                ev1, k1, v1 = dates_seen[0]
                ev2, k2, v2 = dates_seen[1]
                if v1 != v2:
                    contradictions.append({
                        "entity_id": ent.id,
                        "attribute_name": "foundation_date",
                        "source_a_id": ev1.id,
                        "source_a_name": ev1.source_name,
                        "source_a_claim": f"{k1}: {v1} ({ev1.snippet[:120]})",
                        "source_b_id": ev2.id,
                        "source_b_name": ev2.source_name,
                        "source_b_claim": f"{k2}: {v2} ({ev2.snippet[:120]})",
                        "explanation": f"Discrepancy detected for entity '{ent.value}': {ev1.source_name} claims {v1}, whereas {ev2.source_name} claims {v2}. Divergence requires human investigator verification.",
                        "metadata": {"conflicting_values": [v1, v2]}
                    })

        return contradictions
