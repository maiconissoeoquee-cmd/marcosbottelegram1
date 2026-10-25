"""Orquestra os provedores: tempo limite, isolamento de falhas, validação de URLs, deduplicação e cache."""
import asyncio
import logging

from app.search.base import SearchResult
from app.security.url_guard import check_url
from app.services.matcher import normalize

log = logging.getLogger(__name__)


class SearchService:
    def __init__(self, providers, db, settings):
        self.providers = providers
        self.db = db
        self.settings = settings

    async def search(self, query: str, use_cache: bool = True, exclude_urls=()) -> list[SearchResult]:
        key = "q:" + normalize(query)
        if use_cache and not exclude_urls:
            cached = self.db.cache_get(key, self.settings.cache_ttl_seconds)
            if cached is not None:
                return [SearchResult.from_dict(d) for d in cached]

        timeout = self.settings.http_timeout_seconds * 2

        async def run(provider):
            return await asyncio.wait_for(provider.search(query), timeout=timeout)

        outcomes = await asyncio.gather(*(run(p) for p in self.providers), return_exceptions=True)
        results, seen = [], set(exclude_urls)
        for provider, outcome in zip(self.providers, outcomes):
            if isinstance(outcome, BaseException):
                log.warning("provedor %s falhou (%s)", provider.name, type(outcome).__name__)
                continue
            for r in outcome:
                ok, why = check_url(r.url)
                if not ok:
                    log.info("resultado descartado (%s): %s", why, provider.name)
                    continue
                if r.url in seen:
                    continue
                seen.add(r.url)
                results.append(r)
        results = results[:10]
        if use_cache and results:
            self.db.cache_set(key, [r.to_dict() for r in results])
        return results
