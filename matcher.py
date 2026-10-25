"""Normalização de texto e busca aproximada (tolera erros de digitação e acentos)."""
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", (text or "").lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9+ ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def score(query: str, candidate: str) -> float:
    q, c = normalize(query), normalize(candidate)
    if not q or not c or len(q) < 2:
        return 0.0
    if q == c:
        return 1.0
    if c.startswith(q) and (len(c) == len(q) or c[len(q)] == " "):
        return 0.92
    if re.search(rf"(^| ){re.escape(q)}( |$)", c):
        return 0.85
    ratio = SequenceMatcher(None, q, c).ratio()
    if " " not in q:
        token_best = max((SequenceMatcher(None, q, t).ratio() for t in c.split()), default=0.0)
        ratio = max(ratio, token_best * 0.95)
    return ratio if ratio >= 0.6 else 0.0


@dataclass
class Decision:
    kind: str  # "none" | "single" | "clarify"
    items: list


def decide(matches: list[tuple[dict, float]], min_score: float = 0.75) -> Decision:
    strong = [(e, s) for e, s in matches if s >= min_score]
    if not strong:
        return Decision("none", [])
    top_entry, top_score = strong[0]
    if len(strong) == 1 or (top_score >= 0.95 and strong[1][1] < top_score - 0.1):
        return Decision("single", [top_entry])
    return Decision("clarify", [e for e, _ in strong[:4]])
