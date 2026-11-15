
import logging

from fastapi import APIRouter, HTTPException

from app.api.schemas import ChatRequest, ChatResponse
from app.orchestration.graph import graph


logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        result = graph.invoke({
            "message": request.message,
            "user_id": request.user_id,
        })

        return ChatResponse(
            response=result.get("response", ""),
            status=result.get("status", "success"),
            intent=result.get("intent"),
            target_agent=result.get("target_agent"),
            tools_used=result.get("tools_used", []),
            sources=result.get("sources", []),
            error=None if result.get("status") != "error"
            else "Não foi possível processar sua solicitação.",
        )

    except Exception:
        logger.exception(
            "Erro ao processar solicitação. user_id=%s",
            request.user_id,
        )

        raise HTTPException(
            status_code=500,
            detail="Não foi possível processar sua solicitação no momento.",
        )
