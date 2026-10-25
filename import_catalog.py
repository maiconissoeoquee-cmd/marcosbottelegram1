"""Importa entradas novas para data/games.json e data/apps.json, validando cada uma.

Uso (no computador ou no Termux):
    python scripts/import_catalog.py minha_lista.json            # grava
    python scripts/import_catalog.py minha_lista.json --dry-run  # só valida

O arquivo de entrada deve ser uma lista JSON de entradas (mesmo formato de data/games.json).
Entradas com o mesmo "id" substituem as antigas.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import DATA_DIR  # noqa: E402
from app.services.catalog_schema import validate_entries  # noqa: E402


def merge_into(path: Path, new_entries: list[dict]) -> int:
    existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    by_id = {e["id"]: e for e in existing if isinstance(e, dict) and "id" in e}
    for e in new_entries:
        by_id[e["id"]] = e
    ordered = sorted(by_id.values(), key=lambda e: e["title"].lower())
    path.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(ordered)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Importa entradas validadas para o catálogo do Marcos.")
    parser.add_argument("file", help="arquivo JSON com a lista de entradas")
    parser.add_argument("--dry-run", action="store_true", help="apenas valida, sem gravar")
    args = parser.parse_args(argv)

    raw = json.loads(Path(args.file).read_text(encoding="utf-8"))
    valid, errors = validate_entries(raw)
    for err in errors:
        print("REJEITADA:", err)
    print(f"Válidas: {len(valid)} · Rejeitadas: {len(errors)}")
    if args.dry_run or not valid:
        return 0 if not errors else 1

    games = [e for e in valid if e["type"] == "game"]
    apps = [e for e in valid if e["type"] == "app"]
    if games:
        total = merge_into(DATA_DIR / "games.json", games)
        print(f"games.json agora tem {total} entradas")
    if apps:
        total = merge_into(DATA_DIR / "apps.json", apps)
        print(f"apps.json agora tem {total} entradas")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
