from datetime import date, timedelta

import pytest

from app import models


def payload(**overrides):
    data = {
        "restaurant_id": 1,
        "ingredient_id": 1,
        "amount": 2.5,
        "unit": "kg",
        "reason": "spoilage",
    }
    data.update(overrides)
    return data


def test_create_calculates_cost_from_kg(client):
    res = client.post("/api/waste", json=payload())
    assert res.status_code == 201
    body = res.json()
    assert body["quantity_kg"] == 2.5
    assert body["price_per_kg"] == 18.0
    assert body["cost"] == 45.0
    assert body["restaurant_name"] == "Test Restaurant"
    assert body["ingredient_name"] == "Salmon"


def test_create_converts_grams(client):
    body = client.post("/api/waste", json=payload(amount=800, unit="g")).json()
    assert body["quantity_kg"] == pytest.approx(0.8)
    assert body["cost"] == pytest.approx(14.4)


def test_create_converts_pieces(client):
    body = client.post("/api/waste", json=payload(ingredient_id=2, amount=12, unit="pcs")).json()
    assert body["quantity_kg"] == pytest.approx(0.72)
    assert body["cost"] == pytest.approx(2.88)


def test_pieces_rejected_for_ingredient_without_piece_weight(client):
    res = client.post("/api/waste", json=payload(amount=3, unit="pcs"))
    assert res.status_code == 400


def test_unknown_restaurant_or_ingredient_returns_404(client):
    assert client.post("/api/waste", json=payload(restaurant_id=99)).status_code == 404
    assert client.post("/api/waste", json=payload(ingredient_id=99)).status_code == 404


@pytest.mark.parametrize("amount", [0, -1])
def test_non_positive_amount_rejected(client, amount):
    assert client.post("/api/waste", json=payload(amount=amount)).status_code == 422


def test_invalid_reason_rejected(client):
    assert client.post("/api/waste", json=payload(reason="because")).status_code == 422


def test_amount_too_large_rejected(client):
    assert client.post("/api/waste", json=payload(amount=600)).status_code == 400


def test_future_date_rejected(client):
    future = (date.today() + timedelta(days=5)).isoformat()
    assert client.post("/api/waste", json=payload(waste_date=future)).status_code == 400


def test_old_cost_does_not_change_when_price_changes(client, db_session):
    client.post("/api/waste", json=payload())

    salmon = db_session.get(models.Ingredient, 1)
    salmon.price_per_kg = 30.0
    db_session.commit()

    entry = client.get("/api/waste").json()[0]
    assert entry["price_per_kg"] == 18.0
    assert entry["cost"] == 45.0

    # A new entry uses the new price
    new_entry = client.post("/api/waste", json=payload()).json()
    assert new_entry["cost"] == 75.0


def test_list_can_filter_by_restaurant(client):
    client.post("/api/waste", json=payload(restaurant_id=1))
    client.post("/api/waste", json=payload(restaurant_id=2))

    all_entries = client.get("/api/waste").json()
    only_second = client.get("/api/waste", params={"restaurant_id": 2}).json()

    assert len(all_entries) == 2
    assert len(only_second) == 1
    assert only_second[0]["restaurant_name"] == "Second Restaurant"


def test_delete_entry(client):
    entry_id = client.post("/api/waste", json=payload()).json()["id"]

    assert client.delete(f"/api/waste/{entry_id}").status_code == 204
    assert client.get("/api/waste").json() == []
    assert client.delete(f"/api/waste/{entry_id}").status_code == 404


def test_reasons_endpoint(client):
    reasons = client.get("/api/reasons").json()
    assert "spoilage" in reasons
    assert "plate_waste" in reasons