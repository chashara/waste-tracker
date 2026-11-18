from typing import Optional


def to_kg(amount: float, unit: str, grams_per_piece: Optional[float]) -> float:
    """Convert an entered amount (kg, g or pieces) into kilograms."""
    if unit == "kg":
        return amount
    if unit == "g":
        return amount / 1000
    if unit == "pcs":
        if not grams_per_piece:
            raise ValueError("This ingredient has no piece weight, so it can't be entered in pieces.")
        return amount * grams_per_piece / 1000
    raise ValueError(f"Unknown unit: {unit}")


def calculate_cost(quantity_kg: float, price_per_kg: float) -> float:
    """Cost of the waste in euros, rounded to cents."""
    return round(quantity_kg * price_per_kg, 2)