
import time
from pathlib import Path

from google import genai

from app.config import settings


class FileSearchService:
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY não configurada.")

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

        self.store_name = settings.GEMINI_FILE_SEARCH_STORE_NAME.strip()

    def ensure_store(self) -> str:
        """Cria o File Search Store caso ainda não exista."""

        if self.store_name:
            return self.store_name

        store = self.client.file_search_stores.create(
            config={
                "display_name": "Getnet Knowledge Base"
            }
        )

        self.store_name = store.name

        print(f"File Search Store criado: {self.store_name}")
        print(
            "\nAdicione esta variável ao seu .env:\n"
            f"GEMINI_FILE_SEARCH_STORE_NAME={self.store_name}"
        )

        return self.store_name

    def upload_document(
        self,
        file_path: Path,
        display_name: str,
        source_url: str,
        metadata: dict,
    ) -> str:
        """Envia um documento ao File Search e aguarda a indexação."""

        store_name = self.ensure_store()

        custom_metadata = [
            {
                "key": "source_url",
                "string_value": source_url,
            }
        ]

        for key, value in metadata.items():
            custom_metadata.append({
                "key": key,
                "string_value": str(value),
            })

        operation = self.client.file_search_stores.upload_to_file_search_store(
            file=str(file_path),
            file_search_store_name=store_name,
            config={
                "display_name": display_name,
                "mime_type": "text/plain",
                "custom_metadata": custom_metadata,
            },
        )

        while not operation.done:
            time.sleep(2)
            operation = self.client.operations.get(operation)

        if operation.error:
            raise RuntimeError(
                f"Falha ao indexar {display_name}: {operation.error}"
            )

        print(f"Documento indexado: {display_name}")

        return display_name
