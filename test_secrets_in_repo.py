import re
from pathlib import Path

from app.security.secrets import looks_like_secret

ROOT = Path(__file__).resolve().parents[1]
REAL_KEY = re.compile(r"sk-[A-Za-z0-9_\-]{20,}")
REAL_TOKEN = re.compile(r"\b\d{8,12}:[A-Za-z0-9_\-]{30,}\b")


def _project_files():
    for p in ROOT.rglob("*"):
        if p.is_file() and "tests" not in p.parts and "__pycache__" not in p.parts:
            yield p


def test_nao_ha_chaves_ou_tokens_reais_no_projeto():
    for p in _project_files():
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        assert not REAL_KEY.search(text), f"possível chave em {p}"
        assert not REAL_TOKEN.search(text), f"possível token em {p}"


def test_env_real_nao_esta_no_projeto_e_gitignore_protege():
    assert not (ROOT / ".env").exists()
    assert ".env" in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()


def test_env_example_so_tem_placeholders():
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            assert not looks_like_secret(value), key
            if key in ("TELEGRAM_BOT_TOKEN", "OPENAI_API_KEY"):
                assert value.startswith("coloque_"), key
