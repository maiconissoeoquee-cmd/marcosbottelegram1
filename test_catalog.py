import json

from app.config import DATA_DIR
from app.database.db import Database
from app.services.catalog import CatalogService


def _service():
    svc = CatalogService(Database(":memory:"))
    svc.load(DATA_DIR)
    return svc


def _raw_count():
    total = 0
    for name in ("games.json", "apps.json"):
        total += len(json.loads((DATA_DIR / name).read_text(encoding="utf-8")))
    return total


def test_catalogo_inicial_carrega_e_e_valido():
    svc = _service()
    assert svc.count() == _raw_count() > 0


def test_shizuku_e_utilitario_e_nao_jogo():
    e = _service().get("shizuku")
    assert e["type"] == "app" and e["category"] == "utilitario"


def test_busca_no_catalogo_encontra_exemplos():
    svc = _service()
    assert svc.find("Subway Surfers")[0][0]["id"] == "subway-surfers"
    assert svc.find("fifa")[0][0]["id"] == "ea-sports-fc-mobile"


def test_nenhuma_versao_modificada_sem_fonte_verificada():
    for e in _service().entries.values():
        for key in ("mod", "mod_menu"):
            m = e.get(key)
            if m is None:
                continue
            if m["verified"]:
                assert m.get("source"), e["id"]


def test_todas_as_urls_oficiais_sao_https():
    for e in _service().entries.values():
        assert e["official_url"].startswith("https://"), e["id"]


def test_categoria_listada():
    names = [e["title"] for e in _service().by_category("futebol")]
    assert "EA SPORTS FC Mobile" in names
