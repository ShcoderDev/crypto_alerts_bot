from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    tg_id: int
    username: Optional[str]
    registration_date: datetime


@dataclass
class PriceAlert:
    id: Optional[int]
    user_id: int
    cryptocurrency: str
    target_price: float
    is_above: bool  # True если цена должна быть выше, False если ниже
    created_at: datetime
    is_active: bool

