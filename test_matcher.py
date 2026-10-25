from app.services.matcher import decide, normalize, score


def test_normaliza_acentos_e_caixa():
    assert normalize("Vídeo  Editor!") == "video editor"


def test_erro_de_digitacao_ainda_encontra():
    assert score("subwey surfers", "Subway Surfers") >= 0.75


def test_nome_parcial_encontra():
    assert score("subway surf", "Subway Surfers") >= 0.75


def test_nomes_diferentes_nao_casam():
    assert score("minecraft", "Subway Surfers") == 0.0


def test_decide_unico_resultado():
    e = {"id": "a"}
    assert decide([(e, 1.0)]).kind == "single"


def test_decide_ambiguo_pede_esclarecimento():
    a, b = {"id": "forza-horizon"}, {"id": "forza-motorsport"}
    d = decide([(a, 0.85), (b, 0.85)])
    assert d.kind == "clarify" and len(d.items) == 2


def test_decide_sem_resultado_forte():
    assert decide([({"id": "x"}, 0.5)]).kind == "none"
