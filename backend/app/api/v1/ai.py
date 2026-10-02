"""AI Copilot and Gemini Intelligence REST API endpoints."""

from fastapi import APIRouter, HTTPException
from app.schemas.investigation import AIChatRequest, AIChatResponse
from app.ai.gemini_client import gemini_engine

router = APIRouter(prefix="/ai", tags=["AI Copilot"])


@router.post("/chat", response_model=AIChatResponse)
async def chat_with_copilot(payload: AIChatRequest):
    """Interact with the APEX AI Copilot.
    
    Supports modes: INVESTIGATOR, ANALYST, CORRELATOR, RESEARCHER,
    REPORTER, VERIFIER, SUMMARIZER, TIMELINE_ANALYST.
    Uses Google Gemini function calling when configured, or local evidence reasoning.
    """
    try:
        res = await gemini_engine.chat(
            investigation_id=payload.investigation_id,
            user_message=payload.message,
            mode=payload.mode.upper(),
        )
        return AIChatResponse(
            response=res["response"],
            cited_evidence_ids=res.get("cited_evidence_ids", []),
            confidence=res.get("confidence", 0.90),
            classification=res.get("classification", "AI INFERENCE"),
            tool_executed=res.get("tool_executed"),
            tool_args=res.get("tool_args"),
            tool_result=res.get("tool_result"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Copilot error: {str(e)}")
