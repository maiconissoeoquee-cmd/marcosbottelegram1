"""Ponto de entrada: python -m app.main  (modo polling ou webhook, conforme RUN_MODE)."""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import DATA_DIR, Settings, load_settings, validate_settings
from app.database.db import Database
from app.handlers.telegram_handlers import router
from app.search.github_provider import GitHubSearchProvider
from app.search.playstore_provider import PlayStoreSearchProvider
from app.services.ai_service import AIService
from app.services.catalog import CatalogService
from app.services.container import Services
from app.services.search_service import SearchService
from app.services.state import ChatStateStore


def build_services(settings: Settings) -> Services:
    db = Database(settings.db_path)
    catalog = CatalogService(db)
    count = catalog.load(DATA_DIR)
    logging.getLogger("marcos").info("catálogo carregado: %s entradas", count)
    providers = [
        PlayStoreSearchProvider(),
        GitHubSearchProvider(timeout=settings.http_timeout_seconds, max_bytes=settings.http_max_bytes,
                             token=settings.github_token),
    ]
    search = SearchService(providers, db, settings)
    return Services(settings=settings, db=db, catalog=catalog, search=search, ai=AIService(settings))


def build_dispatcher(services: Services) -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(router)
    dp.workflow_data.update(services=services, states=ChatStateStore())
    return dp


def run_webhook(bot: Bot, dp: Dispatcher, settings: Settings) -> None:
    from aiohttp import web
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

    webhook_url = settings.webhook_base_url.rstrip("/") + "/webhook"
    secret = settings.webhook_secret or None

    async def on_startup(bot: Bot):
        await bot.set_webhook(webhook_url, secret_token=secret, drop_pending_updates=True)

    async def health(_request):
        return web.json_response({"ok": True, "service": "marcos"})

    dp.startup.register(on_startup)
    app = web.Application()
    app.router.add_get("/health", health)
    SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=secret).register(app, path="/webhook")
    setup_application(app, dp, bot=bot)
    web.run_app(app, host="0.0.0.0", port=settings.port)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = load_settings()
    problems = validate_settings(settings)
    for p in problems:
        print(p, file=sys.stderr)
    if any(not p.startswith("Aviso") for p in problems):
        return 1

    bot = Bot(settings.telegram_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    services = build_services(settings)
    dp = build_dispatcher(services)
    if settings.run_mode == "webhook":
        run_webhook(bot, dp, settings)
        return 0
    asyncio.run(dp.start_polling(bot))
    return 0


if __name__ == "__main__":
    sys.exit(main())
