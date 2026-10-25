"""Valida as URLs oficiais do catálogo. Sem --online, faz só a checagem local (sem rede).

Uso:
    python scripts/validate_links.py            # checagem local
    python scripts/validate_links.py --online   # também testa se cada link responde
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import httpx  # noqa: E402

from app.config import DATA_DIR  # noqa: E402
from app.security.url_guard import check_url  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--online", action="store_true")
    args = parser.parse_args(argv)
    bad = 0
    total = 0
    for name in ("games.json", "apps.json"):
        path = DATA_DIR / name
        if not path.exists():
            continue
        for entry in json.loads(path.read_text(encoding="utf-8")):
            total += 1
            url = entry.get("official_url", "")
            ok, why = check_url(url)
            if not ok:
                bad += 1
                print(f"[FALHA LOCAL] {entry.get('id')}: {why}")
                continue
            if args.online:
                try:
                    r = httpx.head(url, follow_redirects=False, timeout=10)
                    status = r.status_code
                    print(f"[{status}] {entry.get('id')}")
                    if status >= 400:
                        bad += 1
                except httpx.HTTPError as exc:
                    bad += 1
                    print(f"[ERRO DE REDE] {entry.get('id')}: {type(exc).__name__}")
            else:
                print(f"[ok local] {entry.get('id')}")
    print(f"Verificados: {total} · Problemas: {bad}")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
