"""Intelligence Dossier Report generation and export REST API."""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.investigation import Investigation
from app.models.target import Target
from app.models.entity import Entity
from app.models.evidence import Evidence
from app.models.relationship import Relationship
from app.models.timeline import TimelineEvent
from app.models.contradiction import Contradiction
from app.models.report import Report
from app.schemas.investigation import ReportCreate

router = APIRouter(prefix="/investigations/{investigation_id}/reports", tags=["Reports"])


@router.post("")
async def generate_report(
    investigation_id: str,
    payload: ReportCreate,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Generate a comprehensive, evidence-grounded Intelligence Dossier report."""
    inv = await db.get(Investigation, investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    targets = list((await db.execute(select(Target).where(Target.investigation_id == investigation_id))).scalars().all())
    entities = list((await db.execute(select(Entity).where(Entity.investigation_id == investigation_id))).scalars().all())
    evidence = list((await db.execute(select(Evidence).where(Evidence.investigation_id == investigation_id))).scalars().all())
    relationships = list((await db.execute(select(Relationship).where(Relationship.investigation_id == investigation_id))).scalars().all())
    timeline = list((await db.execute(select(TimelineEvent).where(TimelineEvent.investigation_id == investigation_id).order_by(TimelineEvent.timestamp.asc()))).scalars().all())
    contradictions = list((await db.execute(select(Contradiction).where(Contradiction.investigation_id == investigation_id))).scalars().all())

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    target_str = ", ".join(t.normalized_value for t in targets) or inv.title

    # Markdown Report Generation
    md = f"""# APEX OSINT INTELLIGENCE REPORT
**Classification:** {payload.classification}  
**Date Generated:** {now_str}  
**Investigation ID:** `{inv.id}`  
**Primary Target(s):** {target_str}  
**Investigation Mode:** {inv.mode.upper()} (Depth {inv.depth})  

---

## 1. EXECUTIVE SUMMARY
{inv.summary_json.get('executive_summary', 'Automated defensive reconnaissance completed. Discovered infrastructure endpoints, associated repositories, and public identities grounded in empirical telemetry.')}

- **Total Entities Discovered:** {len(entities)}
- **Total Correlated Links:** {len(relationships)}
- **Total Evidence Records:** {len(evidence)}
- **Detected Contradictions:** {len(contradictions)}

---

## 2. SCOPE & METHODOLOGY
This investigation was conducted utilizing lawful, defensive OSINT collection against publicly accessible infrastructure, DNS records, TLS transparency logs, and code repositories. In accordance with APEX safety boundaries, zero private intrusions or credential harvesting was attempted.

---

## 3. KEY ENTITIES & DISCOVERED ASSETS

| Entity Type | Identifier / Value | Confidence | Provenance Tier |
|:---|:---|:---|:---|
"""
    for e in entities[:25]:
        md += f"| {e.type} | `{e.value}` | {int(e.confidence * 100)}% | {e.provenance_label} |\n"

    md += """
---

## 4. INFRASTRUCTURE & RELATIONSHIPS
The following directed graph relationships were established through deterministic correlation rules and empirical DNS/BGP resolution:

| Source Entity | Edge Relation | Target Entity | Confidence |
|:---|:---|:---|:---|
"""
    for r in relationships[:25]:
        s_val = next((e.value for e in entities if e.id == r.source_entity_id), r.source_entity_id)
        t_val = next((e.value for e in entities if e.id == r.target_entity_id), r.target_entity_id)
        md += f"| `{s_val}` | **{r.relation_type}** | `{t_val}` | {int(r.confidence * 100)}% |\n"

    if contradictions:
        md += """
---

## 5. CONTRADICTIONS & AMBIGUITY MATRIX
> **[CONFLICT DETECTED]** The following conflicting claims were observed between independent sources. Data has not been silently merged:

"""
        for c in contradictions:
            md += f"- **Attribute:** `{c.attribute_name}`\n"
            md += f"  - **Source A ({c.source_a_name}):** {c.source_a_claim}\n"
            md += f"  - **Source B ({c.source_b_name}):** {c.source_b_claim}\n"
            md += f"  - **Analysis:** {c.explanation}\n\n"

    md += """
---

## 6. CHRONOLOGICAL TIMELINE

| Timestamp (UTC) | Event Type | Description |
|:---|:---|:---|
"""
    for te in timeline[:15]:
        t_str = te.timestamp.strftime("%Y-%m-%d")
        md += f"| {t_str} | `{te.event_type}` | {te.title} — {te.description} |\n"

    md += """
---

## 7. EVIDENCE PROVENANCE AUDIT TRAIL
Every factual assertion in this intelligence report is anchored to immutable evidence records:

| Evidence ID | Source | Collection Method | Snippet |
|:---|:---|:---|:---|
"""
    for ev in evidence[:20]:
        md += f"| `{ev.id[:8]}` | {ev.source_name} | {ev.collection_method} | {ev.snippet[:120]}... |\n"

    md += f"""
---
*Generated by APEX OSINT — Intelligence, connected.*
"""

    report = Report(
        investigation_id=inv.id,
        title=f"Intelligence Dossier: {inv.title}",
        classification=payload.classification,
        format=payload.format,
        content_markdown=md,
        summary_json={
            "entities_count": len(entities),
            "evidence_count": len(evidence),
            "relationships_count": len(relationships),
            "contradictions_count": len(contradictions),
        }
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return {
        "id": report.id,
        "title": report.title,
        "classification": report.classification,
        "format": report.format,
        "content_markdown": report.content_markdown,
        "created_at": report.created_at,
    }


@router.get("/export")
async def export_investigation_bundle(investigation_id: str, db: AsyncSession = Depends(get_db)):
    """Export complete case file bundle in JSON format."""
    inv = await db.get(Investigation, investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    entities = list((await db.execute(select(Entity).where(Entity.investigation_id == investigation_id))).scalars().all())
    evidence = list((await db.execute(select(Evidence).where(Evidence.investigation_id == investigation_id))).scalars().all())
    relationships = list((await db.execute(select(Relationship).where(Relationship.investigation_id == investigation_id))).scalars().all())
    timeline = list((await db.execute(select(TimelineEvent).where(TimelineEvent.investigation_id == investigation_id))).scalars().all())
    contradictions = list((await db.execute(select(Contradiction).where(Contradiction.investigation_id == investigation_id))).scalars().all())

    bundle = {
        "apex_osint_version": "1.0.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "investigation": {
            "id": inv.id,
            "title": inv.title,
            "status": inv.status,
            "mode": inv.mode,
            "depth": inv.depth,
            "summary": inv.summary_json,
        },
        "entities": [{"id": e.id, "type": e.type, "value": e.value, "confidence": e.confidence, "label": e.provenance_label} for e in entities],
        "evidence": [{"id": ev.id, "source": ev.source_name, "type": ev.source_type, "snippet": ev.snippet, "confidence": ev.confidence} for ev in evidence],
        "relationships": [{"source": r.source_entity_id, "target": r.target_entity_id, "type": r.relation_type, "confidence": r.confidence} for r in relationships],
        "timeline": [{"timestamp": te.timestamp.isoformat(), "event": te.event_type, "title": te.title} for te in timeline],
        "contradictions": [{"attribute": c.attribute_name, "source_a": c.source_a_name, "source_b": c.source_b_name, "explanation": c.explanation} for c in contradictions]
    }

    return bundle
