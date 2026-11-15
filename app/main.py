
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.api.routes import router
from app.database.models import create_tables
from app.database.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa os recursos necessários para a aplicação."""

    seed_database()

    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Sistema de atendimento multiagente da Getnet com IA.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "application": settings.APP_NAME,
    }
