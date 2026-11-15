
import sqlite3
from pathlib import Path

from app.config import settings


def get_database_path() -> Path:
    """Obtém o caminho do banco a partir da DATABASE_URL."""

    database_url = settings.DATABASE_URL

    if not database_url.startswith("sqlite:///"):
        raise ValueError("Esta implementação utiliza SQLite.")

    database_path = Path(database_url.replace("sqlite:///", "", 1))

    if not database_path.is_absolute():
        database_path = Path.cwd() / database_path

    database_path.parent.mkdir(parents=True, exist_ok=True)

    return database_path


def get_connection():
    """Abre uma conexão com o banco de dados."""

    connection = sqlite3.connect(get_database_path())
    connection.row_factory = sqlite3.Row

    return connection
