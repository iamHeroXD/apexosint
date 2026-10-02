"""1-Click Synthetic Demo Workspace & Investigation generator."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.workspace import Workspace
from app.models.investigation import Investigation
from app.engine.orchestrator import orchestrator

router = APIRouter(prefix="/demo", tags=["Demo Mode"])


@router.post("/launch")
async def launch_demo_investigation(db: AsyncSession = Depends(get_db)):
    """Initialize synthetic workspace and populate 'Apex Demo Corporation' investigation."""
    # Find or create Demo Workspace
    ws_query = await db.execute(select(Workspace).where(Workspace.name == "APEX Demo Workspace"))
    ws = ws_query.scalars().first()
    if not ws:
        ws = Workspace(
            name="APEX Demo Workspace",
            description="Pre-populated sandbox with synthetic evidence for exploration and testing.",
            tags_json=["demo", "synthetic", "sandbox"]
        )
        db.add(ws)
        await db.commit()
        await db.refresh(ws)

    # Create demo investigation
    inv = Investigation(
        workspace_id=ws.id,
        title="Apex Demo Corporation (apex-defense.org)",
        description="Comprehensive synthetic defense reconnaissance case featuring multi-source evidence, contradictions, and graph topology.",
        mode="standard",
        depth=2,
        is_demo=True,
        status="pending"
    )
    db.add(inv)
    await db.commit()
    await db.refresh(inv)

    # Run population
    await orchestrator.run_investigation(inv.id)

    return {
        "status": "ready",
        "workspace_id": ws.id,
        "investigation_id": inv.id,
        "title": inv.title,
    }
