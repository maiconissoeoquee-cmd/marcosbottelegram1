"""Interface comum para provedores de pesquisa. Novos provedores implementam SearchProvider."""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class SearchResult:
    title: str
    url: str
    source: str
    source_trusted: bool  # True = URL veio de uma fonte reconhecida; NÃO significa que o app foi analisado
    note: str
    developer: str | None = None
    version: str | None = None
    checked_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "SearchResult":
        return SearchResult(**d)


class SearchProvider:
    name = "base"

    async def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        raise NotImplementedError
