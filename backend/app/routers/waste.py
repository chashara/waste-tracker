from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_db
from ..services import calculate_cost, to_kg

router = APIRouter(prefix="/api", tags=["waste"])

MAX_ENTRY_KG = 500  # sanity limit for a single entry


def to_out(entry: models.WasteEntry) -> schemas.WasteEntryOut:
    return schemas.WasteEntryOut(
        id=entry.id,
        restaurant_id=entry.restaurant_id,
        restaurant_name=entry.restaurant.name,
        ingredient_id=entry.ingredient_id,
        ingredient_name=entry.ingredient.name,
        category=entry.ingredient.category,
        quantity_kg=entry.quantity_kg,
        price_per_kg=entry.price_per_kg,
        cost=calculate_cost(entry.quantity_kg, entry.price_per_kg),
        reason=entry.reason,
        note=entry.note,
        waste_date=entry.waste_date,
        created_at=entry.created_at,
    )


@router.get("/reasons", response_model=list[str])
def list_reasons():
    return schemas.REASONS


@router.post("/waste", response_model=schemas.WasteEntryOut, status_code=201)
def create_waste(payload: schemas.WasteEntryCreate, db: Session = Depends(get_db)):
    restaurant = db.get(models.Restaurant, payload.restaurant_id)
    if restaurant is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    ingredient = db.get(models.Ingredient, payload.ingredient_id)
    if ingredient is None:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    try:
        quantity_kg = round(to_kg(payload.amount, payload.unit, ingredient.grams_per_piece), 3)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))

    if quantity_kg <= 0:
        raise HTTPException(status_code=400, detail="Amount is too small.")
    if quantity_kg > MAX_ENTRY_KG:
        raise HTTPException(status_code=400, detail=f"Amount is too large (maximum {MAX_ENTRY_KG} kg per entry).")

    waste_date = payload.waste_date or date.today()
    # One day of tolerance, because the server clock (UTC) can be behind Finnish time
    if waste_date > date.today() + timedelta(days=1):
        raise HTTPException(status_code=400, detail="The date can't be in the future.")

    entry = models.WasteEntry(
        restaurant_id=restaurant.id,
        ingredient_id=ingredient.id,
        quantity_kg=quantity_kg,
        price_per_kg=ingredient.price_per_kg,  # price snapshot at this moment
        reason=payload.reason,
        note=(payload.note or "").strip() or None,
        waste_date=waste_date,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return to_out(entry)


@router.get("/waste", response_model=list[schemas.WasteEntryOut])
def list_waste(
    restaurant_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = (
        select(models.WasteEntry)
        .options(joinedload(models.WasteEntry.restaurant), joinedload(models.WasteEntry.ingredient))
        .order_by(models.WasteEntry.waste_date.desc(), models.WasteEntry.id.desc())
        .limit(limit)
    )
    if restaurant_id is not None:
        query = query.where(models.WasteEntry.restaurant_id == restaurant_id)
    if date_from is not None:
        query = query.where(models.WasteEntry.waste_date >= date_from)
    if date_to is not None:
        query = query.where(models.WasteEntry.waste_date <= date_to)

    return [to_out(entry) for entry in db.scalars(query).all()]


@router.delete("/waste/{entry_id}", status_code=204)
def delete_waste(entry_id: int, db: Session = Depends(get_db)):
    entry = db.get(models.WasteEntry, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(entry)
    db.commit()