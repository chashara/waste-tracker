"""Import ingredients and prices from an Excel (.xlsx) or CSV file.

Run from the backend folder, with the virtual environment active:
    python import_prices.py ../data/prices.xlsx --dry-run   # preview, saves nothing
    python import_prices.py ../data/prices.xlsx             # import
    python import_prices.py ../data/prices.xlsx --prune     # also remove unused ingredients that are not in the file

Columns are found by their header. Needed: ingredient name and price per kg.
Optional: "kategoria"/"category" and "g/kpl" (grams per piece).
"""

import argparse
import csv
import re
import sys
from pathlib import Path

from sqlalchemy import func, select

from app import models
from app.database import Base, SessionLocal, engine

NAME_HEADERS = ["raaka", "name", "nimi", "ingredient"]
PRICE_HEADERS = ["hinta", "price", "€"]
CATEGORY_HEADERS = ["kategoria", "category"]
GRAMS_HEADERS = ["g/kpl", "gram", "paino"]


def to_float(value):
    """Read a number from a cell: 12, 12.5, "12,5". Returns None if there isn't one."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().lower().replace(" ", "").replace(",", ".")
    match = re.match(r"^(\d+(?:\.\d+)?)", text)
    return float(match.group(1)) if match else None


def parse_price(value):
    """Returns (amount, is_per_piece, problem).

    Understands 3.75, "3,75", "25,10kg(2,51/pussi)" and "10senttiä/kpl".
    """
    if value is None or str(value).strip() == "":
        return None, False, "no price"
    if isinstance(value, (int, float)):
        return float(value), False, None

    text = str(value).strip().lower().replace("€", "").replace(" ", "").replace(",", ".")
    match = re.match(r"^(\d+(?:\.\d+)?)", text)
    if not match:
        return None, False, f'could not read the price "{value}"'

    amount = float(match.group(1))
    per_piece = "kpl" in text
    if per_piece and ("sent" in text or "snt" in text):
        amount = amount / 100  # cents to euros
    return amount, per_piece, None


def find_column(headers, keywords):
    for index, header in enumerate(headers):
        if header is not None and any(keyword in str(header).lower() for keyword in keywords):
            return index
    return None


def cell(row, index):
    return row[index] if index is not None and index < len(row) else None


def parse_sheet(rows):
    """Turn the rows of a sheet into (items, skipped, names_in_file). Does not touch the database."""
    numbered = [(n, row) for n, row in enumerate(rows, start=1) if any(c not in (None, "") for c in row)]
    if len(numbered) < 2:
        raise ValueError("The file needs a header row and at least one ingredient.")

    headers = numbered[0][1]
    name_col = find_column(headers, NAME_HEADERS)
    price_col = find_column(headers, PRICE_HEADERS)
    name_col = 0 if name_col is None else name_col
    price_col = 1 if price_col is None else price_col
    category_col = find_column(headers, CATEGORY_HEADERS)
    grams_col = find_column(headers, GRAMS_HEADERS)

    items, skipped, names = [], [], set()
    for line, row in numbered[1:]:
        name = " ".join(str(cell(row, name_col) or "").split())
        if not name:
            continue
        key = name.lower()
        if key in names:
            skipped.append((line, name, "appears more than once in the file"))
            continue
        names.add(key)

        raw_price = cell(row, price_col)
        price, per_piece, problem = parse_price(raw_price)
        grams = to_float(cell(row, grams_col))

        if problem is None and per_piece:
            if not grams or grams <= 0:
                problem = f'price is per piece ("{raw_price}"): add the piece weight in grams in a "g/kpl" column'
            else:
                price = price / (grams / 1000)  # euros per kg
        if problem is None and not (0 < price < 1000):
            problem = f"the price {price} looks wrong"
        if problem:
            skipped.append((line, name, problem))
            continue

        category = " ".join(str(cell(row, category_col) or "").split()) or None
        items.append(
            {
                "name": name,
                "price_per_kg": round(price, 2),
                "grams_per_piece": grams if grams and grams > 0 else None,
                "category": category,
            }
        )
    return items, skipped, names


def read_rows(path):
    path = Path(path)
    if not path.exists():
        raise ValueError(f"File not found: {path}")

    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xlsm"):
        from openpyxl import load_workbook

        workbook = load_workbook(path, data_only=True, read_only=True)
        return [list(row) for row in workbook.active.iter_rows(values_only=True)]
    if suffix == ".csv":
        with open(path, encoding="utf-8-sig", newline="") as handle:
            delimiter = ";" if ";" in handle.readline() else ","
            handle.seek(0)
            return [row for row in csv.reader(handle, delimiter=delimiter)]
    raise ValueError("Please use an .xlsx or .csv file.")


def apply_items(db, items, names_in_file, prune):
    existing = {i.name.lower(): i for i in db.scalars(select(models.Ingredient))}
    created = updated = unchanged = 0

    for item in items:
        current = existing.get(item["name"].lower())
        if current is None:
            db.add(
                models.Ingredient(
                    name=item["name"],
                    category=item["category"] or "Other",
                    price_per_kg=item["price_per_kg"],
                    grams_per_piece=item["grams_per_piece"],
                )
            )
            created += 1
            continue

        changed = False
        if abs(current.price_per_kg - item["price_per_kg"]) > 0.001:
            current.price_per_kg = item["price_per_kg"]
            changed = True
        if item["grams_per_piece"] and current.grams_per_piece != item["grams_per_piece"]:
            current.grams_per_piece = item["grams_per_piece"]
            changed = True
        if item["category"] and current.category != item["category"]:
            current.category = item["category"]
            changed = True
        updated += int(changed)
        unchanged += int(not changed)

    removed, kept = [], []
    if prune:
        used = dict(
            db.execute(
                select(models.WasteEntry.ingredient_id, func.count()).group_by(models.WasteEntry.ingredient_id)
            ).all()
        )
        for key, ingredient in existing.items():
            if key in names_in_file:
                continue
            if used.get(ingredient.id):
                kept.append((ingredient.name, used[ingredient.id]))
            else:
                db.delete(ingredient)
                removed.append(ingredient.name)

    return created, updated, unchanged, removed, kept


def main():
    parser = argparse.ArgumentParser(description="Import ingredients and prices from Excel or CSV.")
    parser.add_argument("file", help="path to the .xlsx or .csv file")
    parser.add_argument("--dry-run", action="store_true", help="show what would happen, save nothing")
    parser.add_argument(
        "--prune",
        action="store_true",
        help="remove ingredients that are not in the file and have no waste entries",
    )
    args = parser.parse_args()

    try:
        items, skipped, names = parse_sheet(read_rows(args.file))
    except ValueError as err:
        sys.exit(f"Error: {err}")

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        created, updated, unchanged, removed, kept = apply_items(db, items, names, args.prune)
        if args.dry_run:
            db.rollback()
        else:
            db.commit()

    print("DRY RUN: nothing was saved.\n" if args.dry_run else "Import finished.\n")
    print(f"  Ingredients with a usable price: {len(items)}")
    print(f"  Created:   {created}")
    print(f"  Updated:   {updated}")
    print(f"  Unchanged: {unchanged}")
    print(f"  Skipped:   {len(skipped)}")
    for line, name, reason in skipped:
        print(f'    row {line} "{name}": {reason}')
    if args.prune:
        print(f"  Removed (not in the file, never used): {len(removed)}")
        for name, count in kept:
            print(f'    kept "{name}": it has {count} waste entries')


if __name__ == "__main__":
    main()