"""Provedor GitHub: usa a API pública oficial e devolve apenas repositórios que a própria API retornou."""
import json
from urllib.parse import quote_plus

from app.search.base import SearchProvider, SearchResult
from app.security.http_client import safe_get

API_URL = "https://api.github.com/search/repositories"


class GitHubSearchProvider(SearchProvider):
    name = "github"

    def __init__(self, timeout: float = 8.0, max_bytes: int = 512_000, token: str = ""):
        self.timeout = timeout
        self.max_bytes = max_bytes
        self.token = token

    async def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        q = f"{query} android"
        url = f"{API_URL}?q={quote_plus(q)}&sort=stars&order=desc&per_page={min(max(limit, 1), 10)}"
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "Marcos-Telegram-Bot"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        body = await safe_get(url, timeout=self.timeout, max_bytes=self.max_bytes, headers=headers)
        data = json.loads(body)
        results = []
        for item in (data.get("items") or [])[:limit]:
            html_url, full_name = item.get("html_url"), item.get("full_name")
            if not html_url or not full_name:
                continue
            desc = (item.get("description") or "").strip()
            results.append(SearchResult(
                title=full_name,
                url=html_url,
                source="GitHub (API oficial)",
                source_trusted=True,
                note=("Repositório público encontrado pela API do GitHub; o código não foi analisado. "
                      + desc)[:240],
                developer=(item.get("owner") or {}).get("login"),
            ))
        return results
