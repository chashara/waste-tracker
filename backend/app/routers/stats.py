from collections import defaultdict
from datetime import date, timedelta
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db
from ..schemas_stats import (
    IngredientStatsOut,
    ReasonStatsOut,
    RestaurantStatsOut,
    SummaryOut,
    TrendPointOut,
)

router = APIRouter(prefix="/api/stats", tags=["stats"])

W = models.WasteEntry
COST = func.sum(W.quantity_kg * W.price_per_kg)
KG = func.sum(W.quantity_kg)


def resolve_range(date_from: Optional[date], date_to: Optional[date]):
    """Default range: the last 30 days."""
    end = date_to or date.today()
    start = date_from or end - timedelta(days=29)
    if start > end:
        raise HTTPException(status_code=400, detail="date_from must be on or before date_to.")
    if (end - start).days > 366:
        raise HTTPException(status_code=400, detail="The date range can be at most one year.")
    return start, end


def totals(db: Session, start: date, end: date, restaurant_id: Optional[int] = None):
    query = select(func.coalesce(COST, 0.0), func.coalesce(KG, 0.0), func.count(W.id)).where(
        W.waste_date >= start, W.waste_date <= end
    )
    if restaurant_id is not None:
        query = query.where(W.restaurant_id == restaurant_id)
    cost, kg, count = db.execute(query).one()
    return float(cost), float(kg), int(count)


@router.get("/summary", response_model=SummaryOut)
def summary(
    restaurant_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    compare_from: Optional[date] = None,
    compare_to: Optional[date] = None,
    db: Session = Depends(get_db),
):
    start, end = resolve_range(date_from, date_to)

    if compare_from is not None and compare_to is not None:
        # The caller chose the period to compare with (for example the previous month)
        prev_start, prev_end = resolve_range(compare_from, compare_to)
    else:
        # Default: the period of the same length right before this one
        length = (end - start).days + 1
        prev_end = start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=length - 1)

    cost, kg, count = totals(db, start, end, restaurant_id)
    prev_cost, _, _ = totals(db, prev_start, prev_end, restaurant_id)
    change = round((cost - prev_cost) / prev_cost * 100, 1) if prev_cost > 0 else None

    return SummaryOut(
        date_from=start,
        date_to=end,
        total_cost=round(cost, 2),
        total_kg=round(kg, 2),
        entries=count,
        previous_cost=round(prev_cost, 2),
        change_pct=change,
    )

@router.get("/restaurants", response_model=list[RestaurantStatsOut])
def restaurant_comparison(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
):
    start, end = resolve_range(date_from, date_to)

    waste_rows = db.execute(
        select(W.restaurant_id, COST.label("cost"), KG.label("kg"), func.count(W.id).label("n"))
        .where(W.waste_date >= start, W.waste_date <= end)
        .group_by(W.restaurant_id)
    ).all()
    waste = {row.restaurant_id: row for row in waste_rows}

    result = []
    for restaurant in db.scalars(select(models.Restaurant)).all():
        row = waste.get(restaurant.id)
        result.append(
            RestaurantStatsOut(
                restaurant_id=restaurant.id,
                restaurant_name=restaurant.name,
                total_cost=round(float(row.cost), 2) if row else 0.0,
                total_kg=round(float(row.kg), 2) if row else 0.0,
                entries=int(row.n) if row else 0,
            )
        )
    result.sort(key=lambda item: item.total_cost, reverse=True)
    return result


@router.get("/ingredients", response_model=list[IngredientStatsOut])
def top_ingredients(
    restaurant_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    sort_by: Literal["cost", "kg"] = "cost",
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    start, end = resolve_range(date_from, date_to)
    cost_col = COST.label("cost")
    kg_col = KG.label("kg")

    query = (
        select(
            models.Ingredient.id,
            models.Ingredient.name,
            models.Ingredient.category,
            cost_col,
            kg_col,
            func.count(W.id).label("n"),
        )
        .select_from(W)
        .join(models.Ingredient, models.Ingredient.id == W.ingredient_id)
        .where(W.waste_date >= start, W.waste_date <= end)
        .group_by(models.Ingredient.id, models.Ingredient.name, models.Ingredient.category)
        .order_by((cost_col if sort_by == "cost" else kg_col).desc())
        .limit(limit)
    )
    if restaurant_id is not None:
        query = query.where(W.restaurant_id == restaurant_id)

    return [
        IngredientStatsOut(
            ingredient_id=row.id,
            ingredient_name=row.name,
            category=row.category,
            total_cost=round(float(row.cost), 2),
            total_kg=round(float(row.kg), 2),
            entries=int(row.n),
        )
        for row in db.execute(query).all()
    ]


@router.get("/reasons", response_model=list[ReasonStatsOut])
def by_reason(
    restaurant_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
):
    start, end = resolve_range(date_from, date_to)
    cost_col = COST.label("cost")

    query = (
        select(W.reason, cost_col, KG.label("kg"))
        .where(W.waste_date >= start, W.waste_date <= end)
        .group_by(W.reason)
        .order_by(cost_col.desc())
    )
    if restaurant_id is not None:
        query = query.where(W.restaurant_id == restaurant_id)

    rows = db.execute(query).all()
    grand_total = sum(float(row.cost) for row in rows)
    return [
        ReasonStatsOut(
            reason=row.reason,
            total_cost=round(float(row.cost), 2),
            total_kg=round(float(row.kg), 2),
            share_pct=round(float(row.cost) / grand_total * 100, 1) if grand_total > 0 else 0.0,
        )
        for row in rows
    ]


def bucket_start(day: date, interval: str) -> date:
    if interval == "week":
        return day - timedelta(days=day.weekday())  # Monday
    if interval == "month":
        return day.replace(day=1)
    return day


@router.get("/trend", response_model=list[TrendPointOut])
def trend(
    interval: Literal["day", "week", "month"] = "day",
    restaurant_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
):
    start, end = resolve_range(date_from, date_to)

    query = (
        select(W.restaurant_id, W.waste_date, COST.label("cost"), KG.label("kg"))
        .where(W.waste_date >= start, W.waste_date <= end)
        .group_by(W.restaurant_id, W.waste_date)
    )
    if restaurant_id is not None:
        query = query.where(W.restaurant_id == restaurant_id)

    names = {r.id: r.name for r in db.scalars(select(models.Restaurant))}

    # Group by day in SQL, then roll up to weeks/months in Python.
    # That keeps the code identical for SQLite and PostgreSQL.
    buckets = defaultdict(lambda: [0.0, 0.0])
    for row in db.execute(query).all():
        key = (bucket_start(row.waste_date, interval), row.restaurant_id)
        buckets[key][0] += float(row.cost)
        buckets[key][1] += float(row.kg)

    return [
        TrendPointOut(
            period=period,
            restaurant_id=rid,
            restaurant_name=names.get(rid, "Unknown"),
            cost=round(values[0], 2),
            kg=round(values[1], 2),
        )
        for (period, rid), values in sorted(buckets.items())
    ]