from datetime import date, timedelta

import pytest

from app import models


def add_entry(db, restaurant_id=1, ingredient_id=1, kg=1.0, price=10.0, reason="spoilage", day=None):
    db.add(
        models.WasteEntry(
            restaurant_id=restaurant_id,
            ingredient_id=ingredient_id,
            quantity_kg=kg,
            price_per_kg=price,
            reason=reason,
            waste_date=day or date.today(),
        )
    )
    db.commit()


def test_summary_totals(client, db_session):
    add_entry(db_session, kg=2, price=10)  # 20
    add_entry(db_session, kg=1, price=5)  # 5

    body = client.get("/api/stats/summary").json()
    assert body["total_cost"] == pytest.approx(25.0)
    assert body["total_kg"] == pytest.approx(3.0)
    assert body["entries"] == 2


def test_summary_change_vs_previous_period(client, db_session):
    today = date.today()
    add_entry(db_session, kg=2, price=10, day=today - timedelta(days=2))  # current period: 20
    add_entry(db_session, kg=1, price=10, day=today - timedelta(days=12))  # previous period: 10

    body = client.get(
        "/api/stats/summary",
        params={"date_from": (today - timedelta(days=9)).isoformat(), "date_to": today.isoformat()},
    ).json()
    assert body["total_cost"] == pytest.approx(20.0)
    assert body["previous_cost"] == pytest.approx(10.0)
    assert body["change_pct"] == pytest.approx(100.0)


def test_change_is_none_without_previous_data(client, db_session):
    add_entry(db_session)
    assert client.get("/api/stats/summary").json()["change_pct"] is None


def test_restaurants_are_ranked_and_cost_per_cover_calculated(client, db_session):
    add_entry(db_session, restaurant_id=1, kg=10, price=10)  # 100
    add_entry(db_session, restaurant_id=2, kg=5, price=10)  # 50
    db_session.add(models.DailyCovers(restaurant_id=1, day=date.today(), covers=200))
    db_session.commit()

    rows = client.get("/api/stats/restaurants").json()
    assert [r["restaurant_id"] for r in rows] == [1, 2]
    assert rows[0]["cost_per_cover"] == pytest.approx(0.5)
    assert rows[1]["cost_per_cover"] is None  # no covers recorded


def test_ingredients_can_be_ranked_by_cost_or_weight(client, db_session):
    add_entry(db_session, ingredient_id=1, kg=3, price=18)  # salmon: 54 EUR, 3 kg
    add_entry(db_session, ingredient_id=2, kg=10, price=4)  # eggs: 40 EUR, 10 kg

    by_cost = client.get("/api/stats/ingredients", params={"sort_by": "cost"}).json()
    by_kg = client.get("/api/stats/ingredients", params={"sort_by": "kg"}).json()
    assert by_cost[0]["ingredient_name"] == "Salmon"
    assert by_kg[0]["ingredient_name"] == "Eggs"


def test_ingredients_can_be_filtered_by_restaurant(client, db_session):
    add_entry(db_session, restaurant_id=1, ingredient_id=1)
    add_entry(db_session, restaurant_id=2, ingredient_id=2)

    rows = client.get("/api/stats/ingredients", params={"restaurant_id": 2}).json()
    assert [r["ingredient_name"] for r in rows] == ["Eggs"]


def test_reasons_share_of_total(client, db_session):
    add_entry(db_session, kg=3, price=10, reason="spoilage")  # 30
    add_entry(db_session, kg=1, price=10, reason="trimming")  # 10

    rows = {r["reason"]: r for r in client.get("/api/stats/reasons").json()}
    assert rows["spoilage"]["share_pct"] == pytest.approx(75.0)
    assert rows["trimming"]["share_pct"] == pytest.approx(25.0)


def test_weekly_trend_groups_days_into_one_week(client, db_session):
    today = date.today()
    monday = today - timedelta(days=today.weekday() + 7)  # Monday of last week
    add_entry(db_session, kg=1, price=10, day=monday)
    add_entry(db_session, kg=2, price=10, day=monday + timedelta(days=1))

    points = client.get("/api/stats/trend", params={"interval": "week"}).json()
    assert len(points) == 1
    assert points[0]["period"] == monday.isoformat()
    assert points[0]["cost"] == pytest.approx(30.0)


def test_invalid_date_range_rejected(client):
    res = client.get("/api/stats/summary", params={"date_from": "2026-02-01", "date_to": "2026-01-01"})
    assert res.status_code == 400


def test_set_covers_creates_then_updates(client):
    today = date.today().isoformat()
    first = client.put("/api/covers", json={"restaurant_id": 1, "day": today, "covers": 120})
    second = client.put("/api/covers", json={"restaurant_id": 1, "day": today, "covers": 150})

    assert first.status_code == 200
    assert second.json()["id"] == first.json()["id"]  # same row, updated
    assert second.json()["covers"] == 150


def test_set_covers_unknown_restaurant(client):
    res = client.put("/api/covers", json={"restaurant_id": 99, "day": date.today().isoformat(), "covers": 10})
    assert res.status_code == 404