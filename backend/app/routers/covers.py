from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db

router = APIRouter(prefix="/api", tags=["covers"])


class CoversIn(BaseModel):
    restaurant_id: int
    day: date
    covers: int = Field(ge=0, le=5000)


class CoversOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_id: int
    day: date
    covers: int


@router.put("/covers", response_model=CoversOut)
def set_covers(payload: CoversIn, db: Session = Depends(get_db)):
    """Create or update the number of customers served on a day."""
    if db.get(models.Restaurant, payload.restaurant_id) is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if payload.day > date.today() + timedelta(days=1):
        raise HTTPException(status_code=400, detail="The date can't be in the future.")

    row = db.scalar(
        select(models.DailyCovers).where(
            models.DailyCovers.restaurant_id == payload.restaurant_id,
            models.DailyCovers.day == payload.day,
        )
    )
    if row:
        row.covers = payload.covers
    else:
        row = models.DailyCovers(restaurant_id=payload.restaurant_id, day=payload.day, covers=payload.covers)
        db.add(row)
    db.commit()
    db.refresh(row)
    return row