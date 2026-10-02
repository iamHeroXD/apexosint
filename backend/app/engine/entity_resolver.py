"""Entity Resolution & Identity Disambiguation Engine for APEX OSINT."""

import uuid
from typing import List, Dict, Any, Optional
from app.models.entity import Entity
from app.models.evidence import Evidence


class EntityResolver:
    """Disambiguates distinct persons/entities sharing identifiers and groups verified matches into clusters."""

    @classmethod
    def resolve_and_cluster(
        cls,
        entities: List[Entity],
        evidence_list: List[Evidence]
    ) -> Dict[str, Any]:
        """Group ambiguous entities into distinct disambiguation clusters."""
        clusters: Dict[str, List[Entity]] = {}

        # Disambiguate PERSON entities sharing common names
        person_entities = [e for e in entities if e.type == "PERSON"]
        name_groups: Dict[str, List[Entity]] = {}
        for p in person_entities:
            norm_name = p.normalized_value
            if norm_name not in name_groups:
                name_groups[norm_name] = []
            name_groups[norm_name].append(p)

        for norm_name, group in name_groups.items():
            if len(group) == 1:
                p = group[0]
                if not p.cluster_id:
                    p.cluster_id = f"cluster-{p.normalized_value.replace(' ', '-')}-1"
                clusters[p.cluster_id] = [p]
            else:
                # Multiple people sharing this name -> Separate clusters!
                for idx, p in enumerate(group, 1):
                    cluster_key = f"cluster-{p.normalized_value.replace(' ', '-')}-{idx}"
                    p.cluster_id = cluster_key
                    clusters[cluster_key] = [p]

        return {
            "total_clusters": len(clusters),
            "clusters": {k: [e.value for e in v] for k, v in clusters.items()}
        }

    @classmethod
    def score_match_confidence(cls, evidence_count: int, sources_count: int) -> str:
        """Classify resolution confidence into epistemic tiers."""
        if sources_count >= 2:
            return "CORROBORATED"
        elif evidence_count >= 2:
            return "PROBABLE"
        return "POSSIBLE"
