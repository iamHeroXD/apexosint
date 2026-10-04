"""Investigation Graph visualization and topology REST API."""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.entity import Entity
from app.models.relationship import Relationship

router = APIRouter(prefix="/investigations/{investigation_id}/graph", tags=["Graph Visualizer"])

# Terminal dark color palette mapped to OSINT entity types
ENTITY_COLOR_MAP = {
    "DOMAIN": "#38bdf8",       # Sky blue
    "SUBDOMAIN": "#0ea5e9",    # Deeper blue
    "IP": "#a855f7",           # Purple
    "ASN": "#8b5cf6",          # Violet
    "EMAIL": "#f59e0b",        # Amber
    "USERNAME": "#10b981",     # Emerald
    "PERSON": "#ec4899",       # Rose / Pink
    "ORGANIZATION": "#6366f1", # Indigo
    "REPOSITORY": "#14b8a6",   # Teal
    "CERTIFICATE": "#eab308",  # Yellow
    "DOCUMENT": "#64748b",     # Slate
    "LOCATION": "#f97316",     # Orange
    "SOCIAL_PROFILE": "#06b6d4", # Cyan
    "PHONE_NUMBER": "#84cc16", # Lime
    "CRYPTO_ADDRESS": "#d946ef", # Fuchsia
    "URL": "#3b82f6",          # Blue
}


@router.get("")
async def get_cytoscape_graph(
    investigation_id: str,
    node_type: Optional[str] = None,
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Retrieve graph topology formatted for Cytoscape.js rendering."""
    # Query entities
    entity_q = select(Entity).where(
        Entity.investigation_id == investigation_id,
        Entity.confidence >= min_confidence
    )
    if node_type:
        entity_q = entity_q.where(Entity.type == node_type.upper())
    
    ent_res = await db.execute(entity_q)
    entities = ent_res.scalars().all()
    entity_id_set = {e.id for e in entities}

    # Query relationships
    rel_res = await db.execute(
        select(Relationship).where(
            Relationship.investigation_id == investigation_id,
            Relationship.confidence >= min_confidence
        )
    )
    relationships = rel_res.scalars().all()

    nodes = []
    for ent in entities:
        color = ENTITY_COLOR_MAP.get(ent.type, "#94a3b8")
        nodes.append({
            "data": {
                "id": ent.id,
                "label": ent.value[:30] + "..." if len(ent.value) > 30 else ent.value,
                "full_value": ent.value,
                "type": ent.type,
                "confidence": ent.confidence,
                "provenance_label": ent.provenance_label,
                "cluster_id": ent.cluster_id,
                "color": color,
                "is_bookmarked": ent.is_bookmarked,
                "metadata": ent.metadata_json or {},
            }
        })

    edges = []
    for rel in relationships:
        if rel.source_entity_id in entity_id_set and rel.target_entity_id in entity_id_set:
            edges.append({
                "data": {
                    "id": rel.id,
                    "source": rel.source_entity_id,
                    "target": rel.target_entity_id,
                    "label": rel.relation_type,
                    "confidence": rel.confidence,
                    "discovery_method": rel.discovery_method,
                    "explanation": rel.explanation,
                    "evidence_ids": rel.evidence_ids_json or [],
                    "is_ai_inferred": rel.is_ai_inferred,
                    "evidence_count": len(rel.evidence_ids_json or []),
                }
            })

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "node_types": list(set(e.type for e in entities)),
        }
    }
