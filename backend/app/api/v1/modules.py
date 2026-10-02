"""OSINT Module Health Center and Configuration REST API."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from app.modules.registry import module_registry

router = APIRouter(prefix="/modules", tags=["Module Center"])


@router.get("", response_model=List[Dict[str, Any]])
async def list_modules():
    """Retrieve all registered OSINT modules and their live health metrics."""
    return module_registry.list_modules()


@router.post("/{name}/toggle")
async def toggle_module(name: str):
    """Enable or disable an OSINT module."""
    mod = module_registry.get_module(name)
    if not mod:
        raise HTTPException(status_code=404, detail="Module not found")
    new_state = not mod.enabled
    module_registry.set_module_enabled(name, new_state)
    return {"module": name, "enabled": new_state}
