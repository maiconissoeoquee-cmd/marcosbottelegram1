"""Interpretação por regras locais (funciona sem IA). A IA, quando disponível, tem prioridade."""
import re

from app.services.catalog_schema import CATEGORIES
from app.services.matcher import normalize

ALLOWED_INTENTS = {"search", "select_option", "list_category", "new_source", "latest", "help", "unknown"}

ORDINALS = {
    "primeiro": 1, "primeira": 1, "segundo": 2, "segunda": 2, "terceiro": 3, "terceira": 3,
    "quarto": 4, "quarta": 4, "quinto": 5, "quinta": 5,
}
CATEGORY_WORDS = {
    "futebol": ["futebol", "soccer"],
    "corrida": ["corrida", "corridas", "racing"],
    "tiro": ["tiro", "zumbi", "zumbis", "shooter"],
    "aventura": ["aventura"],
    "rpg": ["rpg"],
    "acao": ["acao", "luta", "lutas"],
    "emulador": ["emulador", "emuladores", "emulacao"],
    "editor_video": ["editor de video", "editores de video", "edicao de video", "editor de imagem"],
    "utilitario": ["utilitario", "utilitarios", "ferramenta", "ferramentas"],
    "redes_sociais": ["rede social", "redes sociais"],
    "navegador": ["navegador", "navegadores", "browser"],
    "produtividade": ["produtividade"],
    "codigo_aberto": ["codigo aberto", "open source", "software livre"],
    "offline": ["offline"],
    "online": ["online"],
}
GREETINGS = {"oi", "ola", "bom dia", "boa tarde", "boa noite", "ajuda", "help", "menu", "start", "oi marcos", "ola marcos"}
NEW_SOURCE_PHRASES = ["outro site", "outra fonte", "outro link", "nao funciona", "nao abre", "procura outro", "procure outro"]
LATEST_PHRASES = ["mais recente", "versao nova", "nova versao", "ultima versao", "atualizada", "atualizacao", "mais atual"]
LIST_RE = re.compile(r"\bquais\b|\blista\b|\bque (jogos|apps|aplicativos)\b|\bo que voce tem\b|\bvoce tem\b")
PREFIX_RE = re.compile(r"^(oi |ei |ola )?(bot )?marcos\b")
FILLER = {
    "me", "manda", "mande", "ai", "pra", "para", "mim", "quero", "queria", "baixar", "baixa", "download",
    "passa", "passe", "procura", "procure", "procurar", "acha", "ache", "tem", "voce", "vc", "o", "a", "os",
    "as", "um", "uma", "aquele", "aquela", "esse", "essa", "este", "esta", "desse", "dessa", "jogo", "app",
    "aplicativo", "aplicativos", "versao", "mais", "recente", "android", "que", "nao", "funciona", "porque",
    "pode", "poderia", "por", "favor", "segundo", "primeiro", "link", "eu", "preciso", "gostaria",
}


def detect_category(n: str) -> str | None:
    for cat, words in CATEGORY_WORDS.items():
        for w in words:
            if re.search(rf"(^| ){re.escape(normalize(w))}s?( |$)", n):
                return cat
    return None


def extract_query(n: str) -> str | None:
    n = PREFIX_RE.sub("", n).strip()
    tokens = [t for t in n.split() if t not in FILLER]
    query = " ".join(tokens).strip()
    return query or None


def parse_rules(text: str) -> dict:
    n = normalize(text or "")
    result = {"intent": "unknown", "query": None, "category": None, "platform": None,
              "ordinal": None, "source": "rules"}
    if not n:
        return result
    if n in GREETINGS:
        result["intent"] = "help"
        return result
    words = n.split()
    ordinal = next((ORDINALS[w] for w in words if w in ORDINALS), None)
    if ordinal and len(words) <= 6:
        result.update(intent="select_option", ordinal=ordinal)
        return result
    if any(p in n for p in NEW_SOURCE_PHRASES):
        result["intent"] = "new_source"
        return result
    category = detect_category(n)
    result["category"] = category
    if "android" in words:
        result["platform"] = "android"
    if any(p in n for p in LATEST_PHRASES):
        result.update(intent="latest", query=extract_query(n))
        return result
    if LIST_RE.search(n):
        result["intent"] = "list_category"
        return result
    query = extract_query(n)
    if query:
        result.update(intent="search", query=query)
    elif category:
        result.update(intent="list_category")
    return result


def sanitize_ai_intent(data, fallback: dict) -> dict:
    """Valida a resposta da IA: sem URLs, intenções e categorias conhecidas, limites de tamanho."""
    if not isinstance(data, dict):
        return fallback
    intent = data.get("intent")
    if intent not in ALLOWED_INTENTS:
        return fallback
    query = data.get("query")
    if isinstance(query, str):
        query = query.strip()[:80] or None
        if query and re.search(r"https?://|www\.|\.[a-z]{2,}/", query, re.I):
            query = None
    else:
        query = None
    if intent == "search" and not query:
        query = fallback.get("query")
    category = data.get("category")
    category = category if category in CATEGORIES else fallback.get("category")
    ordinal = data.get("ordinal")
    if not (isinstance(ordinal, int) and not isinstance(ordinal, bool) and 1 <= ordinal <= 9):
        ordinal = None
    return {"intent": intent, "query": query, "category": category, "platform": None,
            "ordinal": ordinal, "source": "ai"}
