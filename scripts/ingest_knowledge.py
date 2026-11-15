
from app.rag.ingestion import KnowledgeIngestion


URLS = [
    "https://site.getnet.com.br/todas-as-maquininhas/",
    "https://site.getnet.com.br/get-lite/",
    "https://site.getnet.com.br/maquininha/get-classica/",
    "https://site.getnet.com.br/maquininha/get-smart/",
    "https://site.getnet.com.br/taxas/",
    "https://site.getnet.com.br/get-tap/",
    "https://site.getnet.com.br/get-ajuda/",
    "https://www.getnet.net/en/",
]


def main():
    ingestion = KnowledgeIngestion()
    ingestion.ingest_urls(URLS)


if __name__ == "__main__":
    main()
