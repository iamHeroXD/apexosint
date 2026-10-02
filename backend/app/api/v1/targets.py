"""Universal Target Analysis API endpoint."""

from typing import List
from fastapi import APIRouter
from app.engine.universal_detector import UniversalTargetEngine
from app.schemas.investigation import UniversalQueryRequest, AnalyzedTargetOut

router = APIRouter(prefix="/target", tags=["Universal Target Engine"])


@router.post("/analyze", response_model=List[AnalyzedTargetOut])
async def analyze_target_query(payload: UniversalQueryRequest):
    """Universal Target Analyzer.
    
    Accepts any raw user input (single entity or multiple comma-separated entries),
    detects multi-type hypotheses with confidence scores, and formulates an
    investigation plan before launching.
    """
    analyzed_list = UniversalTargetEngine.process_universal_query(payload.query)
    return [a.to_dict() for a in analyzed_list]
