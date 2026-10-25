from app.services.catalog_schema import validate_entries, validate_entry

GOOD = {
    "id": "exemplo-app", "title": "Exemplo", "type": "app", "category": "utilitario",
    "platform": "android", "official_url": "https://example.com/app", "official_source": "Site oficial",
}


def test_entrada_valida_passa():
    valid, errors = validate_entries([GOOD])
    assert len(valid) == 1 and errors == []


def test_url_http_e_rejeitada():
    bad = dict(GOOD, official_url="http://example.com/app")
    valid, errors = validate_entries([bad])
    assert valid == [] and any("official_url" in e for e in errors)


def test_ip_privado_e_rejeitado():
    bad = dict(GOOD, official_url="https://192.168.0.10/app")
    assert validate_entry(bad)


def test_campo_obrigatorio_ausente():
    bad = {k: v for k, v in GOOD.items() if k != "title"}
    assert any("title" in e for e in validate_entry(bad))


def test_categoria_desconhecida_e_rejeitada():
    assert validate_entry(dict(GOOD, category="inventada"))


def test_mod_verificado_sem_fonte_e_rejeitado():
    bad = dict(GOOD, mod={"url": "https://example.com/mod", "source": "", "verified": True})
    assert any("source" in e for e in validate_entry(bad))


def test_ids_duplicados_sao_rejeitados():
    valid, errors = validate_entries([GOOD, GOOD])
    assert len(valid) == 1 and any("duplicado" in e for e in errors)


def test_entrada_nao_objeto():
    valid, errors = validate_entries(["texto"])
    assert valid == [] and errors
