from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    category: Mapped[str] = mapped_column(String(50))
    price_per_kg: Mapped[float] = mapped_column(Float)
    # For items counted in pieces (eggs, bread rolls): average weight of one piece
    grams_per_piece: Mapped[float | None] = mapped_column(Float, nullable=True)


class WasteEntry(Base):
    __tablename__ = "waste_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.id"), index=True)
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id"), index=True)
    quantity_kg: Mapped[float] = mapped_column(Float)
    # The ingredient's price at the moment of entry. Saved here so that changing
    # an ingredient's price later doesn't rewrite the cost of old waste.
    price_per_kg: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(String(30))
    note: Mapped[str | None] = mapped_column(String(200), nullable=True)
    waste_date: Mapped[date] = mapped_column(Date, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    restaurant: Mapped[Restaurant] = relationship()
    ingredient: Mapped[Ingredient] = relationship()