"""Agrupa os serviços compartilhados (injetados nos handlers pelo aiogram)."""
from dataclasses import dataclass
from typing import Any


@dataclass
class Services:
    settings: Any
    db: Any
    catalog: Any
    search: Any
    ai: Any
