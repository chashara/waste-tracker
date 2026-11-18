from datetime import date, datetime
from typing import Literal, Optional, get_args

from pydantic import BaseModel, ConfigDict, Field

Unit = Literal["kg", "g", "pcs"]
Reason = Literal["spoilage", "trimming", "overproduction", "plate_waste", "other"]
REASONS = list(get_args(Reason))


class RestaurantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class IngredientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: str
    price_per_kg: float
    grams_per_piece: Optional[float] = None


class WasteEntryCreate(BaseModel):
    restaurant_id: int
    ingredient_id: int
    amount: float = Field(gt=0, le=10000)
    unit: Unit = "kg"
    reason: Reason
    note: Optional[str] = Field(default=None, max_length=200)
    waste_date: Optional[date] = None  # defaults to today


class WasteEntryOut(BaseModel):
    id: int
    restaurant_id: int
    restaurant_name: str
    ingredient_id: int
    ingredient_name: str
    category: str
    quantity_kg: float
    price_per_kg: float
    cost: float
    reason: str
    note: Optional[str] = None
    waste_date: date
    created_at: datetime