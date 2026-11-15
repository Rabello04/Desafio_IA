
import logging
from pathlib import Path

from google import genai
from google.genai import types, errors
from tavily import TavilyClient

from app.config import settings


logger = logging.getLogger(__name__)


class KnowledgeAgent:
    """Agente responsável por responder perguntas usando RAG e busca web."""

    WEB_SEARCH_MARKER = "NEED_WEB_SEARCH"

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY não configurada.")

        if not settings.GEMINI_FILE_SEARCH_STORE_NAME:
            raise ValueError(
                "GEMINI_FILE_SEARCH_STORE_NAME não configurado."
            )

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

        self.model = settings.GEMINI_MODEL
        self.store_name = settings.GEMINI_FILE_SEARCH_STORE_NAME

        prompt_path = (
            Path(__file__).resolve().parents[1]
            / "prompts"
            / "knowledge.txt"
        )

        self.system_instruction = prompt_path.read_text(
            encoding="utf-8"
        )

    def run(self, message: str) -> dict:
        """Consulta primeiro a base Getnet e depois a web, se necessário."""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=message,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    tools=[
                        types.Tool(
                            file_search=types.FileSearch(
                                file_search_store_names=[
                                    self.store_name
                                ]
                            )
                        )
                    ],
                ),
            )

            answer = response.text or ""

            needs_web_search = (
                not answer.strip()
                or self.WEB_SEARCH_MARKER in answer
            )

            if needs_web_search:
                return self._search_web(message)

            return {
                "response": answer.strip(),
                "status": "success",
                "tools_used": ["gemini_file_search"],
                "sources": self._extract_sources(response),
            }

        except errors.APIError as exc:
            logger.exception(
                "Erro da API Gemini durante consulta ao File Search: %s",
                exc,
            )

            logger.warning(
                "Tentando pesquisa externa com Tavily como alternativa."
            )

            return self._search_web(message)

        except Exception as exc:
            logger.exception(
                "Erro inesperado no Knowledge Agent: %s",
                exc,
            )

            return {
                "response": (
                    "Ocorreu um erro ao consultar a base de conhecimento."
                ),
                "status": "error",
                "tools_used": [],
                "sources": [],
                "error": "Erro interno no Knowledge Agent.",
            }

    def _search_web(self, message: str) -> dict:
        """Realiza pesquisa externa utilizando a API do Tavily."""

        try:
            if not settings.TAVILY_API_KEY:
                raise ValueError("TAVILY_API_KEY não configurada.")

            tavily_client = TavilyClient(
                api_key=settings.TAVILY_API_KEY
            )

            search_response = tavily_client.search(
                query=message,
                search_depth="basic",
                max_results=5,
                include_answer="basic",
            )

            answer = search_response.get("answer") or ""
            sources = self._extract_tavily_sources(search_response)

            # Se não houver resumo, apresenta os resultados encontrados.
            if not answer.strip():
                results = search_response.get("results", [])

                if results:
                    answer = (
                        "Encontrei os seguintes resultados na pesquisa:"
                    )

                    for result in results:
                        title = result.get("title", "Fonte consultada")
                        content = result.get("content", "")

                        answer += (
                            f"\n\n**{title}**\n{content}"
                        )
                else:
                    answer = (
                        "Não encontrei informações suficientes "
                        "para responder à sua pergunta."
                    )

            return {
                "response": (
                    "Informações obtidas por pesquisa externa:\n\n"
                    + answer
                ),
                "status": "success",
                "tools_used": ["tavily_search"],
                "sources": sources,
            }

        except Exception as exc:
            logger.exception(
                "Erro durante pesquisa no Tavily: %s",
                exc,
            )

            return {
                "response": (
                    "Não foi possível realizar a busca na web "
                    "no momento."
                ),
                "status": "error",
                "tools_used": ["tavily_search"],
                "sources": [],
                "error": "Erro na busca externa.",
            }

    @staticmethod
    def _extract_sources(response) -> list[str]:
        """Extrai fontes recuperadas pelo Gemini File Search."""

        sources = []

        try:
            candidates = response.candidates or []

            for candidate in candidates:
                metadata = candidate.grounding_metadata

                if not metadata:
                    continue

                chunks = metadata.grounding_chunks or []

                for chunk in chunks:
                    web_source = chunk.web

                    if not web_source:
                        continue

                    url = web_source.uri
                    title = web_source.title or url

                    if url and not any(
                        source.endswith(f" | {url}")
                        for source in sources
                    ):
                        sources.append(f"{title} | {url}")

        except (AttributeError, TypeError):
            logger.exception(
                "Erro ao extrair fontes do Gemini File Search."
            )

        return sources

    @staticmethod
    def _extract_tavily_sources(response) -> list[str]:
        """Extrai títulos e URLs dos resultados do Tavily."""

        sources = []

        for result in response.get("results", []):
            url = result.get("url")
            title = result.get("title") or url

            if url and url not in [
                source.split(" | ")[-1]
                for source in sources
            ]:
                sources.append(f"{title} | {url}")

        return sources
