from app.services.intent import parse_rules, sanitize_ai_intent


def test_nome_com_apelido_e_pedido_de_manda():
    r = parse_rules("Marcos, me manda o Subway Surfers.")
    assert r["intent"] == "search"
    assert r["query"] == "subway surfers"


def test_app_para_android():
    r = parse_rules("Tem FIFA para Android?")
    assert r["intent"] == "search" and r["query"] == "fifa"


def test_opcao_por_ordinal():
    r = parse_rules("Me manda o segundo link")
    assert r["intent"] == "select_option" and r["ordinal"] == 2


def test_procura_outro_site():
    assert parse_rules("Procura outro site porque esse não funciona")["intent"] == "new_source"


def test_lista_por_categoria():
    r = parse_rules("Quais jogos de futebol você tem?")
    assert r["intent"] == "list_category" and r["category"] == "futebol"


def test_pergunta_de_versao_recente():
    assert parse_rules("Tem uma versão mais recente desse aplicativo?")["intent"] == "latest"


def test_categoria_sem_nome_vira_busca_por_descricao():
    r = parse_rules("Quero baixar um editor de vídeos.")
    assert r["intent"] == "search"
    assert r["category"] == "editor_video"


def test_mensagem_vazia_ou_saudacao():
    assert parse_rules("")["intent"] == "unknown"
    assert parse_rules("oi")["intent"] == "help"
    assert parse_rules("Marcos")["query"] is None


def test_saida_da_ia_com_url_e_descartada():
    fallback = parse_rules("Manda o Shizuku")
    data = {"intent": "search", "query": "https://evil.example/apk", "category": None, "ordinal": None}
    out = sanitize_ai_intent(data, fallback)
    assert out["query"] == "shizuku"
    assert "http" not in (out["query"] or "")


def test_saida_da_ia_com_intencao_desconhecida_usa_regras():
    fallback = parse_rules("Manda o Shizuku")
    assert sanitize_ai_intent({"intent": "executar_comando"}, fallback) == fallback
    assert sanitize_ai_intent("texto solto", fallback) == fallback
