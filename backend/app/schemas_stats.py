from datetime import date
from typing import Optional

from pydantic import BaseModel


class SummaryOut(BaseModel):
    date_from: date
    date_to: date
    total_cost: float
    total_kg: float
    entries: int
    previous_cost: float  # same length period right before this one
    change_pct: Optional[float] = None  # None when there's no previous data to compare with


class RestaurantStatsOut(BaseModel):
    restaurant_id: int
    restaurant_name: str
    total_cost: float
    total_kg: float
    entries: int


class IngredientStatsOut(BaseModel):
    ingredient_id: int
    ingredient_name: str
    category: str
    total_cost: float
    total_kg: float
    entries: int


class ReasonStatsOut(BaseModel):
    reason: str
    total_cost: float
    total_kg: float
    share_pct: float


class TrendPointOut(BaseModel):
    period: date  # first day of the day/week/month
    restaurant_id: int
    restaurant_name: str
    cost: float
    kg: float