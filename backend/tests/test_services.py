import pytest

from app.services import calculate_cost, to_kg


def test_kg_stays_kg():
    assert to_kg(2.5, "kg", None) == 2.5


def test_grams_to_kg():
    assert to_kg(800, "g", None) == 0.8


def test_pieces_to_kg():
    assert to_kg(12, "pcs", 60) == pytest.approx(0.72)


def test_pieces_without_piece_weight_fails():
    with pytest.raises(ValueError):
        to_kg(5, "pcs", None)


def test_unknown_unit_fails():
    with pytest.raises(ValueError):
        to_kg(1, "liters", None)


def test_cost_is_rounded_to_cents():
    assert calculate_cost(0.333, 10) == 3.33
    assert calculate_cost(2.5, 18) == 45.0