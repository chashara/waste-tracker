import pytest

from import_prices import parse_price, parse_sheet


def test_plain_number():
    assert parse_price(3.75) == (3.75, False, None)


def test_decimal_comma_in_text():
    assert parse_price("3,75") == (3.75, False, None)


def test_price_with_extra_text_is_read_as_per_kg():
    price, per_piece, problem = parse_price("25,10kg(2,51/pussi)")
    assert price == pytest.approx(25.10)
    assert per_piece is False
    assert problem is None


def test_price_per_piece_in_cents():
    price, per_piece, problem = parse_price("10senttiä/kpl")
    assert price == pytest.approx(0.10)
    assert per_piece is True
    assert problem is None


def test_missing_price():
    assert parse_price(None)[2] == "no price"
    assert parse_price("   ")[2] == "no price"


def test_unreadable_price():
    assert parse_price("abc")[2] is not None


def test_sheet_imports_good_rows_and_explains_skipped_ones():
    rows = [
        ("raaka-aine", "kilohinta €/kg"),
        ("kurkku", 1.59),
        ("burger sämpylä", "10senttiä/kpl"),
        ("creme franche ", None),
        ("Pico de gallo", "2.94"),
        ("pico de gallo", 3.0),
    ]
    items, skipped, names = parse_sheet(rows)

    assert [i["name"] for i in items] == ["kurkku", "Pico de gallo"]
    reasons = {name: reason for _, name, reason in skipped}
    assert "piece" in reasons["burger sämpylä"]
    assert reasons["creme franche"] == "no price"
    assert "more than once" in reasons["pico de gallo"]
    assert "creme franche" in names  # skipped rows still count as "in the file"


def test_price_per_piece_is_converted_when_the_weight_is_given():
    rows = [
        ("raaka-aine", "kilohinta €/kg", "g/kpl"),
        ("burger sämpylä", "10senttiä/kpl", 70),
    ]
    items, skipped, _ = parse_sheet(rows)

    assert skipped == []
    assert items[0]["price_per_kg"] == pytest.approx(1.43)  # 0.10 EUR / 0.070 kg
    assert items[0]["grams_per_piece"] == 70