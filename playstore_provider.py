"""Provedor Google Play: gera apenas o link oficial de busca. Não raspa a loja e não afirma nada sobre o app."""
from urllib.parse import quote_plus

from app.search.base import SearchProvider, SearchResult


class PlayStoreSearchProvider(SearchProvider):
    name = "google_play"

    async def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        url = f"https://play.google.com/store/search?q={quote_plus(query)}&c=apps"
        return [SearchResult(
            title=f"Buscar “{query}” na Google Play",
            url=url,
            source="Google Play (busca oficial)",
            source_trusted=True,
            note="Link de busca oficial. O app específico não foi verificado; confira o desenvolvedor na loja.",
        )]
