
import hashlib
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from app.rag.file_search import FileSearchService


SOURCE_METADATA = {
    "https://site.getnet.com.br/todas-as-maquininhas/": {
        "audience": "BOTH",
        "category": "product_catalog",
        "source_type": "commercial",
        "country": "BR",
    },
    "https://site.getnet.com.br/get-lite/": {
        "audience": "UNSPECIFIED",
        "category": "card_machine",
        "source_type": "product",
        "country": "BR",
    },
    "https://site.getnet.com.br/maquininha/get-classica/": {
        "audience": "UNSPECIFIED",
        "category": "card_machine",
        "source_type": "product",
        "country": "BR",
    },
    "https://site.getnet.com.br/maquininha/get-smart/": {
        "audience": "UNSPECIFIED",
        "category": "card_machine",
        "source_type": "product",
        "country": "BR",
    },
    "https://site.getnet.com.br/taxas/": {
        "audience": "UNSPECIFIED",
        "category": "fees",
        "source_type": "commercial",
        "country": "BR",
    },
    "https://site.getnet.com.br/get-tap/": {
        "audience": "UNSPECIFIED",
        "category": "payment_solution",
        "source_type": "product",
        "country": "BR",
    },
    "https://site.getnet.com.br/get-ajuda/": {
        "audience": "BOTH",
        "category": "support",
        "source_type": "documentation",
        "country": "BR",
    },
    "https://www.getnet.net/en/": {
        "audience": "GLOBAL",
        "category": "institutional",
        "source_type": "institutional",
        "country": "GLOBAL",
    },
}


class KnowledgeIngestion:

    def __init__(self):
        self.file_search = FileSearchService()

        self.output_directory = Path("data/knowledge_sources")
        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.headers = {
            "User-Agent": "GetnetMultiAgent/1.0"
        }

    def extract_text(self, url: str) -> str:
        """Extrai e limpa o conteúdo textual de uma página."""

        response = requests.get(
            url,
            headers=self.headers,
            timeout=30,
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        for element in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "noscript",
            "svg",
        ]):
            element.decompose()

        content = (
            soup.find("main")
            or soup.find("article")
            or soup.body
        )

        if content is None:
            raise ValueError(
                f"Nenhum conteúdo HTML encontrado em: {url}"
            )

        return content.get_text(
            separator="\n",
            strip=True,
        )

    def get_source_metadata(self, url: str) -> dict:
        """Retorna os metadados associados à fonte."""

        return SOURCE_METADATA.get(
            url,
            {
                "audience": "UNSPECIFIED",
                "category": "general",
                "source_type": "unknown",
                "country": "UNKNOWN",
            },
        )

    def ingest_url(self, url: str) -> int:
        """Extrai uma URL e envia seu conteúdo ao Gemini File Search."""

        print(f"\nProcessando: {url}")

        text = self.extract_text(url)

        if not text.strip():
            print("Nenhum texto encontrado.")
            return 0

        source_hash = hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest()

        url_hash = hashlib.sha256(
            url.encode("utf-8")
        ).hexdigest()[:12]

        file_path = (
            self.output_directory
            / f"{url_hash}_{source_hash[:12]}.txt"
        )

        file_path.write_text(
            f"Fonte: {url}\n\n{text}",
            encoding="utf-8",
        )

        metadata = self.get_source_metadata(url)

        display_name = f"getnet_{url_hash}.txt"

        self.file_search.upload_document(
            file_path=file_path,
            display_name=display_name,
            source_url=url,
            metadata=metadata,
        )

        print(f"Texto extraído: {len(text)} caracteres")
        print(f"Arquivo preparado: {file_path}")
        print(f"Categoria: {metadata['category']}")

        return 1

    def ingest_urls(self, urls: list[str]) -> int:
        """Executa a ingestão de várias URLs."""

        successful = 0
        failed = 0

        for url in urls:
            try:
                successful += self.ingest_url(url)

            except Exception as error:
                failed += 1
                print(f"Erro ao processar {url}: {error}")

        print("\n--- RESUMO DA INGESTÃO ---")
        print(f"Fontes indexadas: {successful}")
        print(f"Fontes com erro: {failed}")

        if self.file_search.store_name:
            print(
                f"File Search Store: {self.file_search.store_name}"
            )

        return successful
