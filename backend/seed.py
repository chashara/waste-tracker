from sqlalchemy import select

from app import models
from app.database import Base, SessionLocal, engine

RESTAURANTS = ["Ratina", "Duo", "Palokka", "Seppa", "Sokkari"]

# (name, category, price per kg in EUR, grams per piece or None). All prices are fake.
INGREDIENTS = [
    ("Beef mince", "Meat", 11.50, None),
    ("Chicken breast", "Meat", 9.80, None),
    ("Pork belly", "Meat", 8.90, None),
    ("Bacon", "Meat", 12.40, None),
    ("Lamb shoulder", "Meat", 16.00, None),
    ("Salmon fillet", "Fish", 18.50, None),
    ("Cod fillet", "Fish", 17.00, None),
    ("Shrimp", "Fish", 21.00, None),
    ("Butter", "Dairy", 9.20, None),
    ("Cream", "Dairy", 4.80, None),
    ("Mozzarella", "Dairy", 8.50, None),
    ("Parmesan", "Dairy", 22.00, None),
    ("Eggs", "Dairy", 3.60, 60),
    ("Tomato", "Vegetables", 3.80, None),
    ("Potato", "Vegetables", 1.40, None),
    ("Onion", "Vegetables", 1.20, None),
    ("Carrot", "Vegetables", 1.30, None),
    ("Lettuce", "Vegetables", 4.20, None),
    ("Mushroom", "Vegetables", 7.50, None),
    ("Bell pepper", "Vegetables", 5.60, None),
    ("Cucumber", "Vegetables", 2.90, None),
    ("Garlic", "Vegetables", 8.00, None),
    ("Avocado", "Vegetables", 7.00, 200),
    ("Lemon", "Fruit", 3.90, 100),
    ("Banana", "Fruit", 2.20, 120),
    ("Strawberry", "Fruit", 9.00, None),
    ("Bread rolls", "Bakery", 5.00, 70),
    ("Sourdough bread", "Bakery", 6.50, None),
    ("Tortilla wraps", "Bakery", 6.00, 60),
    ("Pasta", "Dry goods", 2.10, None),
    ("Rice", "Dry goods", 1.90, None),
    ("Flour", "Dry goods", 1.10, None),
    ("Sugar", "Dry goods", 1.30, None),
    ("Cooking oil", "Other", 3.20, None),
    ("French fries (frozen)", "Other", 2.60, None),
    ("Tomato sauce", "Other", 2.40, None),
]


def seed():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        existing = set(db.scalars(select(models.Restaurant.name)))
        for name in RESTAURANTS:
            if name not in existing:
                db.add(models.Restaurant(name=name))

        existing = set(db.scalars(select(models.Ingredient.name)))
        for name, category, price, grams in INGREDIENTS:
            if name not in existing:
                db.add(
                    models.Ingredient(
                        name=name, category=category, price_per_kg=price, grams_per_piece=grams
                    )
                )
        db.commit()
    print(f"Seeded {len(RESTAURANTS)} restaurants and {len(INGREDIENTS)} ingredients (if missing).")


if __name__ == "__main__":
    seed()