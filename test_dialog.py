import asyncio

from app.config import DATA_DIR, Settings
from app.database.db import Database
from app.search.base import SearchResult
from app.services import dialog
from app.services.ai_service import AIService
from app.services.catalog import CatalogService
from app.services.container import Services
from app.services.intent import parse_rules
from app.services.presenter import Opt
from app.services.state import ChatState


class FakeSearch:
    def __init__(self, results):
        self.results = results

    async def search(self, query, use_cache=True, exclude_urls=()):
        return [r for r in self.results if r.url not in exclude_urls]


def _services(results=()):
    settings = Settings()
    db = Database(":memory:")
    catalog = CatalogService(db)
    catalog.load(DATA_DIR)
    return Services(settings, db, catalog, FakeSearch(list(results)), AIService(settings))


def _say(services, state, text):
    return asyncio.run(dialog.handle(parse_rules(text), state, services))


def test_app_conhecido_mostra_opcoes_e_nao_inventa_mod():
    svc, st = _services(), ChatState()
    reply = _say(svc, st, "Marcos, me manda o Subway Surfers.")
    assert "Subway Surfers" in reply.text and "Original" in reply.text
    assert reply.keyboard is not None


def test_mod_sem_fonte_verificada_informa_indisponivel():
    svc, st = _services(), ChatState()
    reply = dialog.from_callback(Opt(action="mod", ref="subway-surfers"), st, svc)
    assert "Não foi possível verificar" in reply.text


def test_app_desconhecido_vai_para_busca_e_avisa_que_nao_foi_baixado():
    found = [SearchResult("Editor X", "https://fonte.example/x", "GitHub", True, "nota")]
    svc, st = _services(found), ChatState()
    reply = _say(svc, st, "Quero baixar um editor de videos muito raro")
    assert "nenhum arquivo foi baixado" in reply.text
    assert "Editor X" in reply.text


def test_opcao_inexistente_e_tratada():
    svc = _services([SearchResult("A", "https://a.example", "F", True, "n"),
                     SearchResult("B", "https://b.example", "F", True, "n")])
    st = ChatState()
    _say(svc, st, "Procura um app qualquer zzz")
    reply = _say(svc, st, "manda o quinto")
    assert "Só tenho 2" in reply.text


def test_mensagem_ambigua_sem_nome_pede_nome():
    svc, st = _services(), ChatState()
    reply = _say(svc, st, "Marcos")
    assert "Me diga o nome do jogo" in reply.text


def test_lista_por_categoria_futebol():
    svc, st = _services(), ChatState()
    reply = _say(svc, st, "Quais jogos de futebol você tem?")
    assert "EA SPORTS FC Mobile" in reply.text


def test_segundo_link_sem_lista_aberta():
    svc, st = _services(), ChatState()
    reply = _say(svc, st, "Me manda o segundo link")
    assert "Não tenho uma lista aberta" in reply.text
