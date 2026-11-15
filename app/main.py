
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# Permite a comunicação entre o frontend React e a API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "application": settings.APP_NAME,
    }
