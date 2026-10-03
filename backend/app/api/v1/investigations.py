"""Investigation management and execution REST endpoints."""

import asyncio
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
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
from app.schemas.investigation import (
    InvestigationCreate,
    InvestigationOut,
    EntityOut,
    EvidenceOut,
    RelationshipOut,
    TimelineEventOut,
    ContradictionOut,
)
from app.engine.universal_detector import UniversalTargetEngine
from app.engine.orchestrator import orchestrator
from app.core.events import event_bus

router = APIRouter(prefix="/investigations", tags=["Investigations"])


@router.post("", response_model=InvestigationOut)
async def create_investigation(payload: InvestigationCreate, db: AsyncSession = Depends(get_db)):
    """Create a new investigation using universal query input."""
    inv = Investigation(
        workspace_id=payload.workspace_id,
        title=payload.title,
        mode=payload.mode,
        depth=payload.depth,
        is_demo=payload.is_demo,
        status="pending",
    )
    db.add(inv)
    await db.commit()
    await db.refresh(inv)

    # Process universal query into targets
    analyzed_targets = UniversalTargetEngine.process_universal_query(payload.target_query)
    for at in analyzed_targets:
        tgt = Target(
            investigation_id=inv.id,
            raw_input=at.raw_input,
            detected_type=at.primary_type,
            normalized_value=at.normalized_value,
            confidence=at.primary_confidence,
            hypotheses_json=[h.to_dict() for h in at.hypotheses],
            depth=0,
            status="pending",
        )
        db.add(tgt)

    await db.commit()
    return inv


@router.get("", response_model=List[InvestigationOut])
async def list_investigations(workspace_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """List investigations, optionally filtered by workspace."""
    query = select(Investigation).order_by(Investigation.created_at.desc())
    if workspace_id:
        query = query.where(Investigation.workspace_id == workspace_id)
    res = await db.execute(query)
    return res.scalars().all()


@router.get("/{investigation_id}", response_model=InvestigationOut)
async def get_investigation(investigation_id: str, db: AsyncSession = Depends(get_db)):
    """Get investigation details and summary stats."""
    inv = await db.get(Investigation, investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return inv


@router.post("/{investigation_id}/run")
async def run_investigation(
    investigation_id: str,
    wait: bool = Query(False, description="Wait for investigation to complete before responding"),
    timeout: float = Query(25.0, description="Max seconds to wait if wait=True"),
    db: AsyncSession = Depends(get_db)
):
    """Start or resume investigation execution, optionally waiting for completion."""
    inv = await db.get(Investigation, investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    if not orchestrator.is_running(investigation_id):
        await orchestrator.run_investigation(investigation_id)

    if wait:
        await orchestrator.wait_for_investigation(investigation_id, timeout=timeout)
        await db.refresh(inv)

    is_active = orchestrator.is_running(investigation_id)
    return {
        "status": "completed" if not is_active and inv.status == "completed" else ("running" if is_active else inv.status),
        "investigation_id": investigation_id
    }



@router.post("/{investigation_id}/stop")
async def stop_investigation(investigation_id: str, db: AsyncSession = Depends(get_db)):
    """Pause or cancel active investigation."""
    stopped = orchestrator.cancel_investigation(investigation_id)
    return {"status": "stopped" if stopped else "not_running", "investigation_id": investigation_id}


@router.delete("/purge")
async def purge_all_investigations(db: AsyncSession = Depends(get_db)):
    """Wipe all investigations and historical telemetry for complete zero-trace anonymous operation."""
    from sqlalchemy import delete
    from app.models.investigation import Investigation
    await db.execute(delete(Investigation))
    await db.commit()
    return {"status": "purged", "message": "All investigation history and footprints completely wiped."}


@router.delete("/{investigation_id}")
async def delete_investigation(investigation_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a single investigation and all its associated data."""
    inv = await db.get(Investigation, investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    await db.delete(inv)
    await db.commit()
    return {"status": "deleted", "id": investigation_id}


@router.get("/{investigation_id}/entities", response_model=List[EntityOut])
async def list_entities(
    investigation_id: str,
    type: Optional[str] = None,
    bookmarked: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """List discovered entities with optional filters."""
    q = select(Entity).where(Entity.investigation_id == investigation_id)
    if type:
        q = q.where(Entity.type == type.upper())
    if bookmarked is not None:
        q = q.where(Entity.is_bookmarked == bookmarked)
    res = await db.execute(q)
    return res.scalars().all()


@router.get("/{investigation_id}/evidence", response_model=List[EvidenceOut])
async def list_evidence(
    investigation_id: str,
    source_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List evidence provenance records."""
    q = select(Evidence).where(Evidence.investigation_id == investigation_id).order_by(Evidence.collected_at.desc())
    if source_type:
        q = q.where(Evidence.source_type == source_type.upper())
    res = await db.execute(q)
    return res.scalars().all()


@router.get("/{investigation_id}/relationships", response_model=List[RelationshipOut])
async def list_relationships(investigation_id: str, db: AsyncSession = Depends(get_db)):
    """List graph edges."""
    res = await db.execute(select(Relationship).where(Relationship.investigation_id == investigation_id))
    return res.scalars().all()


@router.get("/{investigation_id}/timeline", response_model=List[TimelineEventOut])
async def list_timeline(investigation_id: str, db: AsyncSession = Depends(get_db)):
    """List chronological timeline events."""
    res = await db.execute(
        select(TimelineEvent)
        .where(TimelineEvent.investigation_id == investigation_id)
        .order_by(TimelineEvent.timestamp.asc())
    )
    return res.scalars().all()


@router.get("/{investigation_id}/contradictions", response_model=List[ContradictionOut])
async def list_contradictions(investigation_id: str, db: AsyncSession = Depends(get_db)):
    """List detected contradictions."""
    res = await db.execute(
        select(Contradiction).where(Contradiction.investigation_id == investigation_id)
    )
    return res.scalars().all()


@router.get("/{investigation_id}/dossier")
async def get_investigation_dossier(investigation_id: str):
    """Retrieve full Persona & Multi-Site Intelligence Dossier synthesized by AI."""
    from app.ai.gemini_client import gemini_engine
    return await gemini_engine.synthesize_comprehensive_dossier(investigation_id)



@router.get("/{investigation_id}/stream")
async def stream_investigation_events(investigation_id: str):
    """Server-Sent Events (SSE) live telemetry stream."""
    queue = await event_bus.subscribe(investigation_id)

    async def event_generator():
        try:
            # Send initial keepalive
            yield f"data: {json.dumps({'type': 'connected', 'investigation_id': investigation_id})}\n\n"
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=25.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive ping
                    yield f": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            await event_bus.unsubscribe(investigation_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
