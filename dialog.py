"""Decide a resposta a partir da intenção, do contexto da conversa e do catálogo/busca."""
from app.services import presenter
from app.services.matcher import decide
from app.services.presenter import Reply

NOT_UNDERSTOOD = (
    'Não entendi bem 🙂 Me diga o nome do jogo ou aplicativo que você procura. '
    'Ex.: "Marcos, manda o Shizuku".'
)


async def handle(intent: dict, state, services) -> Reply:
    kind = intent.get("intent")
    if kind == "help":
        return Reply(presenter.HELP)
    if kind == "select_option":
        return _select(intent.get("ordinal") or 1, state, services)
    if kind == "list_category":
        return _list(intent.get("category"), state, services)
    if kind == "latest":
        return _latest(state, services)
    if kind == "new_source":
        return await _new_source(state, services)
    if kind == "search":
        return await _search(intent.get("query"), state, services)
    return Reply(NOT_UNDERSTOOD)


async def _search(query, state, services) -> Reply:
    if not query:
        return Reply("Qual jogo ou aplicativo você procura? Pode mandar o nome, mesmo com erro de digitação.")
    state.last_query = query
    state.last_entry_id = None
    state.active_kind, state.active_list = None, []
    decision = decide(services.catalog.find(query))
    if decision.kind == "single":
        entry = decision.items[0]
        state.last_entry_id = entry["id"]
        return presenter.option_card(entry)
    if decision.kind == "clarify":
        state.active_kind, state.active_list = "entries", [e["id"] for e in decision.items]
        return presenter.clarify(query, decision.items)
    results = await services.search.search(query)
    return _set_external(query, results, state)


def _set_external(query, results, state) -> Reply:
    state.active_kind, state.active_list = "external", list(results)
    if not results:
        return Reply(f"Não encontrei fontes verificáveis para “{presenter.esc(query)}”. "
                     "Tente o nome oficial do app ou o nome do desenvolvedor.")
    return presenter.external_list(query, results)


def _select(ordinal: int, state, services) -> Reply:
    if state.active_kind == "external" and state.active_list:
        if ordinal > len(state.active_list):
            return Reply(f"Só tenho {len(state.active_list)} opções nessa lista.")
        return presenter.external_detail(state.active_list[ordinal - 1])
    if state.active_kind == "entries" and state.active_list:
        if ordinal > len(state.active_list):
            return Reply(f"Só tenho {len(state.active_list)} opções nessa lista.")
        entry = services.catalog.get(state.active_list[ordinal - 1])
        if entry:
            state.last_entry_id = entry["id"]
            return presenter.option_card(entry)
    if state.last_entry_id:
        if ordinal > 3:
            return Reply("Para este app existem só 3 opções: Original, Modificada e Mod menu.")
        entry = services.catalog.get(state.last_entry_id)
        kind = ["orig", "mod", "menu"][ordinal - 1]
        return presenter.describe(entry, kind)
    return Reply("Não tenho uma lista aberta agora. Qual app ou jogo você procura?")


def _list(category, state, services) -> Reply:
    if not category:
        return presenter.categories()
    entries = services.catalog.by_category(category)
    if not entries:
        return Reply("Ainda não tenho esse grupo no catálogo. Me diga o nome do app que quer "
                     "e eu procuro na internet.")
    state.active_kind, state.active_list = "entries", [e["id"] for e in entries]
    lines = [f"{i}. {presenter.esc(e['title'])}" for i, e in enumerate(entries, 1)]
    return Reply("Aqui estão os que tenho:\n" + "\n".join(lines) + '\nDiga "manda o primeiro" para abrir um deles.')


def _latest(state, services) -> Reply:
    entry = services.catalog.get(state.last_entry_id) if state.last_entry_id else None
    if not entry:
        return Reply("De qual app você quer saber a versão mais recente?")
    return presenter.latest_note(entry)


async def _new_source(state, services) -> Reply:
    if not state.last_query:
        return Reply("Qual app você procura? Assim eu busco outra fonte.")
    exclude = [r.url for r in state.active_list] if state.active_kind == "external" else []
    results = await services.search.search(state.last_query, use_cache=False, exclude_urls=exclude)
    return _set_external(state.last_query, results, state)


def from_callback(opt, state, services) -> Reply:
    if opt.action == "ext":
        i = int(opt.ref) if opt.ref.isdigit() else -1
        if state.active_kind == "external" and 0 <= i < len(state.active_list):
            return presenter.external_detail(state.active_list[i])
        return Reply("Essa lista expirou. Faça a busca de novo.")
    entry = services.catalog.get(opt.ref)
    if not entry:
        return Reply("Não encontrei esse item de novo. Faça a busca outra vez.")
    state.last_entry_id = entry["id"]
    if opt.action == "entry":
        return presenter.option_card(entry)
    if opt.action in ("orig", "mod", "menu"):
        return presenter.describe(entry, opt.action)
    return Reply(NOT_UNDERSTOOD)
