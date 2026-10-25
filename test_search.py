import asyncio

from app.config import Settings
from app.database.db import Database
from app.search.base import SearchProvider, SearchResult
from app.services.search_service import SearchService


class GoodProvider(SearchProvider):
    name = "bom"

    async def search(self, query, limit=5):
        return [SearchResult("App A", "https://fonte.example/a", "Fonte", True, "Repositório encontrado.")]


class InsecureProvider(SearchProvider):
    name = "inseguro"

    async def search(self, query, limit=5):
        return [SearchResult("App B", "http://fonte.example/b", "Fonte", True, "nota"),
                SearchResult("App C", "https://192.168.0.1/c", "Fonte", True, "nota")]


class BrokenProvider(SearchProvider):
    name = "quebrado"

    async def search(self, query, limit=5):
        raise RuntimeError("falha de rede simulada")


def test_resultados_inseguros_sao_descartados_e_falhas_isoladas():
    svc = SearchService([GoodProvider(), InsecureProvider(), BrokenProvider()],
                        Database(":memory:"), Settings())
    results = asyncio.run(svc.search("app teste"))
    assert [r.url for r in results] == ["https://fonte.example/a"]


def test_resultado_de_busca_nao_e_descrito_como_baixado():
    svc = SearchService([GoodProvider()], Database(":memory:"), Settings())
    r = asyncio.run(svc.search("app teste"))[0]
    assert "baixado" not in r.note.lower()
    assert "instalado" not in r.note.lower()
