from pydantic import BaseModel, Field, ConfigDict


class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


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


class TokenUsageResponse(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class ChatResponse(BaseModel):
    response: str
    status: str
    intent: str | None = None
    target_agent: str | None = None
    tools_used: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    token_usage: TokenUsageResponse = Field(default_factory=TokenUsageResponse)
    error: str | None = None
