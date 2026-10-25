"""Handlers do aiogram: recebem mensagens e botões e delegam para o diálogo."""
import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, LinkPreviewOptions, Message

from app.security.secrets import looks_like_secret
from app.services import dialog
from app.services.presenter import HELP, WELCOME, Opt, Reply

router = Router(name="marcos")
log = logging.getLogger(__name__)
NO_PREVIEW = LinkPreviewOptions(is_disabled=True)


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(WELCOME, link_preview_options=NO_PREVIEW)


@router.message(Command("ajuda"))
async def cmd_help(message: Message):
    await message.answer(HELP, link_preview_options=NO_PREVIEW)


@router.message(F.text)
async def on_text(message: Message, services, states):
    text = message.text.strip()
    if looks_like_secret(text):
        await message.answer(
            "🔒 Por segurança, não aceito chaves de API nem tokens aqui. Apague essa mensagem. "
            "Esses dados devem ficar só nas variáveis de ambiente do serviço."
        )
        return
    text = text[: services.settings.max_input_chars]
    chat_id = message.chat.id
    state = states.get(chat_id)
    recent = services.db.recent_messages(chat_id)
    services.db.save_message(chat_id, "user", text)
    intent = await services.ai.interpret(text, recent=recent)
    try:
        reply = await dialog.handle(intent, state, services)
    except Exception:
        log.exception("falha ao responder")
        reply = Reply("Tive um problema para buscar agora. Tente de novo em instantes.")
    await message.answer(reply.text, reply_markup=reply.keyboard, link_preview_options=NO_PREVIEW)


@router.callback_query(Opt.filter())
async def on_option(callback: CallbackQuery, callback_data: Opt, services, states):
    if callback.message is None:
        await callback.answer("Essa mensagem expirou. Faça a busca de novo.", show_alert=True)
        return
    reply = dialog.from_callback(callback_data, states.get(callback.message.chat.id), services)
    await callback.message.answer(reply.text, reply_markup=reply.keyboard, link_preview_options=NO_PREVIEW)
    await callback.answer()
