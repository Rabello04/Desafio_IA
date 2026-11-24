import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
)
from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    LoginRequest,
    TokenResponse,
)
from app.orchestration.graph import graph


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse)
def login(request: LoginRequest):
    authenticated = authenticate_user(
        request.username,
        request.password,
    )

    if not authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(request.username)

    return TokenResponse(access_token=token)


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    user_id: str = Depends(get_current_user),
):
    try:
        result = graph.invoke({
            "message": request.message,
            "user_id": user_id,
        })

        return ChatResponse(
            response=result.get("response", ""),
            status=result.get("status", "success"),
            intent=result.get("intent"),
            target_agent=result.get("target_agent"),
            tools_used=result.get("tools_used", []),
            sources=result.get("sources", []),
            token_usage=result.get("token_usage", {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
            }),
            error=None if result.get("status") != "error"
            else "Não foi possível processar sua solicitação.",
        )

    except Exception:
        logger.exception(
            "Erro ao processar solicitação. user_id=%s",
            user_id,
        )

        raise HTTPException(
            status_code=500,
            detail="Não foi possível processar sua solicitação no momento.",
        )