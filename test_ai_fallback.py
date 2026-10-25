import asyncio
import json
from types import SimpleNamespace

from app.config import Settings
from app.services.ai_service import AIService
from app.services.intent import parse_rules


class FakeCompletions:
    def __init__(self, content):
        self.content = content

    async def create(self, **kwargs):
        if isinstance(self.content, Exception):
            raise self.content
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))])


class FakeClient:
    def __init__(self, content):
        self.chat = SimpleNamespace(completions=FakeCompletions(content))


def _run(service, text):
    return asyncio.run(service.interpret(text))


def test_sem_chave_usa_regras_locais():
    svc = AIService(Settings(openai_api_key=""))
    assert svc.enabled is False
    assert _run(svc, "Manda o Shizuku") == parse_rules("Manda o Shizuku")


def test_ia_fora_do_ar_cai_para_regras():
    svc = AIService(Settings(openai_api_key="x"), client=FakeClient(ConnectionError("sem rede")))
    assert _run(svc, "Manda o Shizuku")["query"] == "shizuku"


def test_resposta_que_nao_e_json_cai_para_regras():
    svc = AIService(Settings(openai_api_key="x"), client=FakeClient("isto não é json"))
    assert _run(svc, "Tem FIFA para Android?")["query"] == "fifa"


def test_ia_valida_e_usada_quando_boa():
    payload = json.dumps({"intent": "search", "query": "Subway Surfers", "category": None, "ordinal": None})
    svc = AIService(Settings(openai_api_key="x"), client=FakeClient(payload))
    out = _run(svc, "manda o subwey surfer")
    assert out["source"] == "ai" and out["query"] == "Subway Surfers"
