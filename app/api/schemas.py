
from pydantic import BaseModel, Field, ConfigDict


class ChatRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Mensagem enviada pelo cliente.",
    )

    user_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Identificador do cliente.",
    )


class ChatResponse(BaseModel):
    response: str
    status: str
    intent: str | None = None
    target_agent: str | None = None
    tools_used: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    error: str | None = None
