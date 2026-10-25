"""Detecção e redação de segredos (chaves de API e tokens do Telegram)."""
import re

_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"\b\d{8,12}:[A-Za-z0-9_\-]{30,}\b"),
]


def looks_like_secret(text: str) -> bool:
    return any(p.search(text or "") for p in _PATTERNS)


def redact(text: str, secrets: list[str]) -> str:
    out = text or ""
    for s in secrets:
        if s and len(s) >= 6:
            out = out.replace(s, "[REDIGIDO]")
    for p in _PATTERNS:
        out = p.sub("[REDIGIDO]", out)
    return out
