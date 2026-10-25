"""Configuração a partir de variáveis de ambiente (nunca grave segredos no código)."""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"


@dataclass
class Settings:
    telegram_token: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    db_path: str = str(ROOT_DIR / "marcos.db")
    run_mode: str = "polling"  # "polling" ou "webhook"
    webhook_base_url: str = ""
    webhook_secret: str = ""
    port: int = 8080
    cache_ttl_seconds: int = 3600
    max_input_chars: int = 500
    ai_timeout_seconds: float = 15.0
    ai_max_retries: int = 1
    http_timeout_seconds: float = 8.0
    http_max_bytes: int = 512_000
    github_token: str = ""
    allow_http_links: bool = False


def _int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _float(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_settings() -> Settings:
    load_dotenv(ROOT_DIR / ".env")
    g = os.environ.get
    return Settings(
        telegram_token=g("TELEGRAM_BOT_TOKEN", "").strip(),
        openai_api_key=g("OPENAI_API_KEY", "").strip(),
        openai_model=g("OPENAI_MODEL", "gpt-4o-mini").strip(),
        db_path=g("DB_PATH", str(ROOT_DIR / "marcos.db")),
        run_mode=g("RUN_MODE", "polling").strip().lower(),
        webhook_base_url=g("WEBHOOK_BASE_URL", "").strip(),
        webhook_secret=g("WEBHOOK_SECRET", "").strip(),
        port=_int(g("PORT", "8080"), 8080),
        cache_ttl_seconds=_int(g("CACHE_TTL_SECONDS", "3600"), 3600),
        max_input_chars=_int(g("MAX_INPUT_CHARS", "500"), 500),
        ai_timeout_seconds=_float(g("AI_TIMEOUT_SECONDS", "15"), 15.0),
        ai_max_retries=_int(g("AI_MAX_RETRIES", "1"), 1),
        http_timeout_seconds=_float(g("HTTP_TIMEOUT_SECONDS", "8"), 8.0),
        http_max_bytes=_int(g("HTTP_MAX_BYTES", "512000"), 512_000),
        github_token=g("GITHUB_TOKEN", "").strip(),
        allow_http_links=g("ALLOW_HTTP_LINKS", "false").strip().lower() in {"1", "true", "sim", "yes"},
    )


def validate_settings(s: Settings) -> list[str]:
    problems = []
    if not s.telegram_token:
        problems.append("TELEGRAM_BOT_TOKEN não configurado (cadastre nas variáveis de ambiente do serviço).")
    if s.run_mode not in {"polling", "webhook"}:
        problems.append("RUN_MODE deve ser 'polling' ou 'webhook'.")
    if s.run_mode == "webhook" and not s.webhook_base_url.startswith("https://"):
        problems.append("No modo webhook, WEBHOOK_BASE_URL precisa começar com https://.")
    if not s.openai_api_key:
        problems.append("Aviso: OPENAI_API_KEY vazia. O bot usará apenas as regras locais de interpretação.")
    return problems
