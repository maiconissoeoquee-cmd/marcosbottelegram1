"""Monta as mensagens em HTML e os botões. Nunca apresenta um resultado como baixado ou analisado."""
import html
from dataclasses import dataclass

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.security.url_guard import check_url
from app.services.catalog_schema import CATEGORY_LABELS


class Opt(CallbackData, prefix="opt"):
    action: str  # entry | orig | mod | menu | ext
    ref: str


@dataclass
class Reply:
    text: str
    keyboard: InlineKeyboardMarkup | None = None


HELP = (
    "Oi! Eu sou o Marcos 🤖\n\n"
    "Me diga o nome do jogo ou app do jeito que preferir. Exemplos:\n"
    "• Marcos, me manda o Subway Surfers.\n"
    "• Manda o Shizuku.\n"
    "• Tem FIFA para Android?\n"
    "• Quero baixar um editor de vídeos.\n"
    "• Quais jogos de futebol você tem?\n\n"
    'Depois de uma busca, use os botões ou diga "manda o segundo". '
    'Se um link não funcionar, diga "procura outro site".\n\n'
    "⚠️ Baixe sempre de fontes oficiais. Eu nunca executo APKs automaticamente."
)
WELCOME = HELP


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def verified_link(entry: dict, key: str) -> dict | None:
    m = entry.get(key)
    if isinstance(m, dict) and m.get("verified") is True and check_url(str(m.get("url", "")))[0]:
        return m
    return None


def option_keyboard(entry: dict) -> InlineKeyboardMarkup:
    row = [InlineKeyboardButton(text="1️⃣ Original", callback_data=Opt(action="orig", ref=entry["id"]).pack())]
    if verified_link(entry, "mod"):
        row.append(InlineKeyboardButton(text="2️⃣ Modificada", callback_data=Opt(action="mod", ref=entry["id"]).pack()))
    if verified_link(entry, "mod_menu"):
        row.append(InlineKeyboardButton(text="3️⃣ Mod menu", callback_data=Opt(action="menu", ref=entry["id"]).pack()))
    return InlineKeyboardMarkup(inline_keyboard=[row])


def option_card(entry: dict) -> Reply:
    text = f"Encontrei <b>{esc(entry['title'])}</b>! Qual versão você procura?\n\n1. Original"
    text += "\n2. Versão modificada" if verified_link(entry, "mod") else "\n2. Versão modificada: não verificada"
    text += "\n3. Mod menu" if verified_link(entry, "mod_menu") else "\n3. Mod menu: não verificado"
    return Reply(text, option_keyboard(entry))


def describe(entry: dict, kind: str) -> Reply:
    title = esc(entry["title"])
    if kind == "orig":
        kind_label = "Jogo" if entry["type"] == "game" else "Aplicativo"
        category = esc(CATEGORY_LABELS.get(entry["category"], entry["category"]))
        url = esc(entry["official_url"])
        lines = [
            f"<b>{title}</b>",
            f"Tipo: {kind_label} · Categoria: {category} · Android",
            f"Desenvolvedor: {esc(entry.get('developer')) or 'não verificado'}",
            f"Versão: {esc(entry.get('version')) or 'não verificada'}",
            f'Fonte oficial: <a href="{url}">{esc(entry["official_source"])}</a>',
            f"Última verificação: {esc(entry.get('last_verified')) or 'não verificada ao vivo'}",
            "Baixe sempre pela fonte oficial.",
        ]
        return Reply("\n".join(lines), option_keyboard(entry))

    label = "Versão modificada" if kind == "mod" else "Mod menu"
    key = "mod" if kind == "mod" else "mod_menu"
    m = verified_link(entry, key)
    if not m:
        return Reply(
            f"Não foi possível verificar uma opção «{label}» com fonte confiável para <b>{title}</b>. "
            "Prefira a versão original.",
            option_keyboard(entry),
        )
    link = esc(m["url"])
    text = (
        f"⚠️ <b>{label}</b> de <b>{title}</b> — modificação NÃO oficial.\n"
        f'Fonte: <a href="{link}">{esc(m.get("source"))}</a>\n'
        "Eu não analisei o conteúdo deste arquivo. Antes de instalar, confira a origem, "
        "nunca informe contas ou senhas e não execute APK sem conferir."
    )
    return Reply(text, option_keyboard(entry))


def clarify(query: str, entries: list[dict]) -> Reply:
    lines = [f"Encontrei mais de um resultado parecido com “{esc(query)}”. Qual deles?"]
    buttons = []
    for i, e in enumerate(entries, 1):
        lines.append(f"{i}. {esc(e['title'])}")
        buttons.append(InlineKeyboardButton(text=f"{i}. {e['title'][:28]}", callback_data=Opt(action="entry", ref=e["id"]).pack()))
    return Reply("\n".join(lines), InlineKeyboardMarkup(inline_keyboard=[[b] for b in buttons]))


def external_list(query: str, results) -> Reply:
    lines = [
        f"Não tenho “{esc(query)}” no catálogo, mas encontrei estas fontes. "
        "Elas são resultados de busca: ainda não foram verificadas uma a uma e nenhum arquivo foi baixado ou analisado."
    ]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {esc(r.title)} — {esc(r.source)}")
    lines.append('Diga "manda o segundo" para ver os detalhes de um deles.')
    row = [InlineKeyboardButton(text=str(i), callback_data=Opt(action="ext", ref=str(i - 1)).pack())
           for i in range(1, len(results) + 1)]
    return Reply("\n".join(lines), InlineKeyboardMarkup(inline_keyboard=[row]))


def external_detail(r) -> Reply:
    url = esc(r.url)
    lines = [
        f"<b>{esc(r.title)}</b>",
        f"Fonte: {esc(r.source)}",
        f'Link: <a href="{url}">{url}</a>',
        f"Desenvolvedor: {esc(r.developer) or 'não informado pela fonte'}",
        f"Observação: {esc(r.note)}",
        f"Consultado em: {esc(r.checked_at)}",
        "Confira o desenvolvedor e as permissões antes de instalar.",
    ]
    return Reply("\n".join(lines))


def categories() -> Reply:
    labels = ", ".join(CATEGORY_LABELS.values())
    return Reply(f"Tenho estas categorias: {labels}. Qual você quer ver?")


def latest_note(entry: dict) -> Reply:
    if entry.get("version"):
        text = f"No meu catálogo, a versão de <b>{esc(entry['title'])}</b> é {esc(entry['version'])}."
    else:
        text = (f"Não tenho uma versão verificada de <b>{esc(entry['title'])}</b>. "
                "Confira a versão mais recente na fonte oficial.")
    return Reply(text + f'\n<a href="{esc(entry["official_url"])}">Abrir fonte oficial</a>')
