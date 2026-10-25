"""Catálogo local: lê data/*.json, valida, espelha no SQLite e oferece busca."""
import json
import logging
from pathlib import Path

from app.services.catalog_schema import validate_entries
from app.services.matcher import score

log = logging.getLogger(__name__)
CATALOG_FILES = ("games.json", "apps.json")


class CatalogService:
    def __init__(self, db):
        self.db = db
        self.entries: dict[str, dict] = {}

    def load(self, data_dir: Path) -> int:
        collected = []
        for name in CATALOG_FILES:
            path = Path(data_dir) / name
            if not path.exists():
                continue
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                log.error("JSON inválido em %s: %s", name, exc)
                continue
            valid, errors = validate_entries(raw)
            for err in errors:
                log.warning("catálogo (%s): %s", name, err)
            collected.extend(valid)
        self.db.catalog_replace(collected)
        self.entries = {e["id"]: e for e in self.db.catalog_all()}
        return len(self.entries)

    def count(self) -> int:
        return len(self.entries)

    def get(self, entry_id: str) -> dict | None:
        return self.entries.get(entry_id)

    def find(self, query: str, min_score: float = 0.6) -> list[tuple[dict, float]]:
        results = []
        for entry in self.entries.values():
            best = max([score(query, entry["title"])] + [score(query, a) for a in entry.get("aliases", [])])
            if best >= min_score:
                results.append((entry, best))
        results.sort(key=lambda pair: pair[1], reverse=True)
        return results

    def by_category(self, category: str) -> list[dict]:
        return sorted((e for e in self.entries.values() if e["category"] == category), key=lambda e: e["title"])
