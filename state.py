"""Contexto de cada conversa em memória (último app, lista aberta). Histórico longo fica no SQLite."""
from dataclasses import dataclass, field


@dataclass
class ChatState:
    last_query: str | None = None
    last_entry_id: str | None = None
    active_kind: str | None = None  # "external" | "entries" | None
    active_list: list = field(default_factory=list)


class ChatStateStore:
    MAX_CHATS = 1000

    def __init__(self):
        self._states: dict[int, ChatState] = {}

    def get(self, chat_id: int) -> ChatState:
        if chat_id not in self._states:
            if len(self._states) >= self.MAX_CHATS:
                self._states.pop(next(iter(self._states)))
            self._states[chat_id] = ChatState()
        return self._states[chat_id]
