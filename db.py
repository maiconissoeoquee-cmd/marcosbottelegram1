"""Banco SQLite local: histórico mínimo, cache de pesquisa e catálogo."""
import json
import sqlite3
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    text TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS search_cache (
    key TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS catalog (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    payload TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def save_message(self, chat_id: int, role: str, text: str) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO messages (chat_id, role, text, created_at) VALUES (?, ?, ?, ?)",
                (chat_id, role, text[:1000], time.time()),
            )
            # Histórico pequeno: no máximo 50 mensagens por conversa.
            self.conn.execute(
                "DELETE FROM messages WHERE chat_id = ? AND id NOT IN "
                "(SELECT id FROM messages WHERE chat_id = ? ORDER BY id DESC LIMIT 50)",
                (chat_id, chat_id),
            )

    def recent_messages(self, chat_id: int, limit: int = 6) -> list[dict]:
        rows = self.conn.execute(
            "SELECT role, text FROM messages WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
            (chat_id, limit),
        ).fetchall()
        return [{"role": r["role"], "text": r["text"]} for r in reversed(rows)]

    def cache_get(self, key: str, ttl: int) -> list | None:
        row = self.conn.execute("SELECT payload, created_at FROM search_cache WHERE key = ?", (key,)).fetchone()
        if not row or time.time() - row["created_at"] > ttl:
            return None
        return json.loads(row["payload"])

    def cache_set(self, key: str, payload: list) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO search_cache (key, payload, created_at) VALUES (?, ?, ?)",
                (key, json.dumps(payload, ensure_ascii=False), time.time()),
            )

    def catalog_replace(self, entries: list[dict]) -> None:
        with self.conn:
            self.conn.execute("DELETE FROM catalog")
            self.conn.executemany(
                "INSERT INTO catalog (id, kind, payload) VALUES (?, ?, ?)",
                [(e["id"], e["type"], json.dumps(e, ensure_ascii=False)) for e in entries],
            )

    def catalog_all(self) -> list[dict]:
        rows = self.conn.execute("SELECT payload FROM catalog ORDER BY id").fetchall()
        return [json.loads(r["payload"]) for r in rows]

    def close(self) -> None:
        self.conn.close()
