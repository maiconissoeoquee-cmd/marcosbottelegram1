"""Regras de validação do catálogo (usadas pelo bot e pelo importador)."""
import re

from app.security.url_guard import check_url

CATEGORY_LABELS = {
    "acao": "Ação", "aventura": "Aventura", "rpg": "RPG", "corrida": "Corrida",
    "futebol": "Futebol", "tiro": "Tiro", "offline": "Offline", "online": "Online",
    "emulador": "Emuladores", "redes_sociais": "Redes sociais", "navegador": "Navegador",
    "editor_video": "Editor de vídeo e imagem", "utilitario": "Utilitário Android",
    "produtividade": "Produtividade", "codigo_aberto": "Código aberto",
}
CATEGORIES = set(CATEGORY_LABELS)
TYPES = {"game", "app"}
REQUIRED = ("id", "title", "type", "category", "platform", "official_url", "official_source")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")


def validate_entry(e) -> list[str]:
    if not isinstance(e, dict):
        return ["entrada não é um objeto"]
    eid = e.get("id", "?")
    errs = []
    for key in REQUIRED:
        if not isinstance(e.get(key), str) or not e.get(key, "").strip():
            errs.append(f"{eid}: campo obrigatório ausente ou vazio: {key}")
    if errs:
        return errs
    if not ID_RE.match(e["id"]):
        errs.append(f"{eid}: id inválido (use letras minúsculas, números, '-' ou '_')")
    if e["type"] not in TYPES:
        errs.append(f"{eid}: type deve ser 'game' ou 'app'")
    if e["category"] not in CATEGORIES:
        errs.append(f"{eid}: categoria desconhecida: {e['category']}")
    if e["platform"] != "android":
        errs.append(f"{eid}: platform deve ser 'android'")
    ok, why = check_url(e["official_url"])
    if not ok:
        errs.append(f"{eid}: official_url inválida ({why})")
    if "aliases" in e and not (isinstance(e["aliases"], list) and all(isinstance(a, str) for a in e["aliases"])):
        errs.append(f"{eid}: aliases deve ser uma lista de textos")
    for key in ("mod", "mod_menu"):
        m = e.get(key)
        if m is None:
            continue
        if not isinstance(m, dict) or not isinstance(m.get("verified"), bool):
            errs.append(f"{eid}: {key} precisa ser objeto com 'verified' booleano")
            continue
        ok, why = check_url(str(m.get("url", "")))
        if not ok:
            errs.append(f"{eid}: {key}.url inválida ({why})")
        if m["verified"] and not m.get("source"):
            errs.append(f"{eid}: {key} verificado precisa informar 'source'")
    return errs


def validate_entries(entries) -> tuple[list[dict], list[str]]:
    if not isinstance(entries, list):
        return [], ["o arquivo deve conter uma lista de entradas"]
    valid, errors, seen = [], [], set()
    for e in entries:
        errs = validate_entry(e)
        if not errs and e["id"] in seen:
            errs.append(f"{e['id']}: id duplicado")
        if errs:
            errors.extend(errs)
            continue
        seen.add(e["id"])
        valid.append(e)
    return valid, errors
