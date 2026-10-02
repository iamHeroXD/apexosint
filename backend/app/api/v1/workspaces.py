"""Workspace REST API routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.workspace import Workspace
from app.models.investigation import Investigation
from app.schemas.investigation import WorkspaceCreate, WorkspaceOut

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.get("", response_model=List[WorkspaceOut])
async def list_workspaces(db: AsyncSession = Depends(get_db)):
    """Retrieve all investigation workspaces."""
    query = await db.execute(select(Workspace).order_by(Workspace.created_at.desc()))
    workspaces = query.scalars().all()
    results = []
    for ws in workspaces:
        # Count investigations
        inv_count_q = await db.execute(
            select(func.count(Investigation.id)).where(Investigation.workspace_id == ws.id)
        )
        count = inv_count_q.scalar() or 0
        results.append(
            WorkspaceOut(
                id=ws.id,
                name=ws.name,
                description=ws.description,
                created_at=ws.created_at,
                investigations_count=count
            )
        )
    return results


@router.post("", response_model=WorkspaceOut)
async def create_workspace(payload: WorkspaceCreate, db: AsyncSession = Depends(get_db)):
    """Create a new investigation workspace."""
    ws = Workspace(
        name=payload.name,
        description=payload.description,
        tags_json=payload.tags,
    )
    db.add(ws)
    await db.commit()
    await db.refresh(ws)
    return WorkspaceOut(
        id=ws.id,
        name=ws.name,
        description=ws.description,
        created_at=ws.created_at,
        investigations_count=0
    )


@router.get("/{workspace_id}", response_model=WorkspaceOut)
async def get_workspace(workspace_id: str, db: AsyncSession = Depends(get_db)):
    """Get workspace details."""
    ws = await db.get(Workspace, workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    inv_count_q = await db.execute(
        select(func.count(Investigation.id)).where(Investigation.workspace_id == ws.id)
    )
    count = inv_count_q.scalar() or 0
    return WorkspaceOut(
        id=ws.id,
        name=ws.name,
        description=ws.description,
        created_at=ws.created_at,
        investigations_count=count
    )
