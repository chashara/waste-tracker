import random
from datetime import date, timedelta

from sqlalchemy import delete, func, select

from app import models
from app.database import SessionLocal
from seed import seed as seed_base

DAYS = 90

# Each restaurant gets a "personality" so the dashboard has something to compare.
# All of this is invented demo data.
PROFILES = {
    "Harbour": {  # seafood-heavy, busy, lots of spoilage
        "waste_volume": 1.0, "covers": 170, "weekend_waste": 1.2, "weekend_covers": 1.3, "trend": 0.0,
        "categories": {"Fish": 3.0},
        "reasons": {"spoilage": 5, "trimming": 3, "overproduction": 2, "plate_waste": 1, "other": 0.5},
    },
    "Old Town": {  # well run: low waste
        "waste_volume": 0.55, "covers": 120, "weekend_waste": 1.1, "weekend_covers": 1.2, "trend": 0.0,
        "categories": {},
        "reasons": {"trimming": 4, "spoilage": 2, "overproduction": 1, "plate_waste": 1, "other": 0.5},
    },
    "Lakeside": {  # quiet weekdays, big weekend overproduction
        "waste_volume": 0.9, "covers": 90, "weekend_waste": 2.2, "weekend_covers": 1.8, "trend": 0.0,
        "categories": {"Bakery": 2.0, "Dairy": 1.5},
        "reasons": {"overproduction": 6, "spoilage": 2, "trimming": 1, "plate_waste": 1, "other": 0.5},
    },
    "Central": {  # biggest and wastiest, lots of plate waste
        "waste_volume": 1.5, "covers": 230, "weekend_waste": 1.1, "weekend_covers": 1.1, "trend": 0.0,
        "categories": {"Meat": 1.8, "Dry goods": 1.5},
        "reasons": {"plate_waste": 6, "spoilage": 3, "overproduction": 2, "trimming": 1, "other": 0.5},
    },
    "Northside": {  # improving over time
        "waste_volume": 1.0, "covers": 110, "weekend_waste": 1.2, "weekend_covers": 1.3, "trend": -0.9,
        "categories": {"Vegetables": 2.0},
        "reasons": {"trimming": 4, "spoilage": 3, "overproduction": 2, "plate_waste": 1, "other": 0.5},
    },
}


def generate():
    rng = random.Random(42)  # fixed seed: same data every run
    seed_base()  # make sure restaurants and ingredients exist
    today = date.today()

    with SessionLocal() as db:
        # Demo data only: this wipes ALL existing waste entries and covers
        db.execute(delete(models.WasteEntry))
        db.execute(delete(models.DailyCovers))

        ingredients = db.scalars(select(models.Ingredient)).all()
        restaurants = {r.name: r for r in db.scalars(select(models.Restaurant))}

        for name, profile in PROFILES.items():
            restaurant = restaurants.get(name)
            if restaurant is None:
                continue

            ingredient_weights = [profile["categories"].get(i.category, 1.0) for i in ingredients]
            reason_names = list(profile["reasons"])
            reason_weights = list(profile["reasons"].values())

            for offset in range(DAYS):
                day = today - timedelta(days=DAYS - 1 - offset)
                weekend = day.weekday() >= 5
                progress = offset / (DAYS - 1)
                trend_factor = 1 + profile["trend"] * (progress - 0.5)

                covers_mean = profile["covers"] * (profile["weekend_covers"] if weekend else 1)
                covers = max(20, round(rng.gauss(covers_mean, profile["covers"] * 0.1)))
                db.add(models.DailyCovers(restaurant_id=restaurant.id, day=day, covers=covers))

                expected = 6 * profile["waste_volume"] * (profile["weekend_waste"] if weekend else 1) * trend_factor
                for _ in range(max(0, round(rng.gauss(expected, 1.5)))):
                    ingredient = rng.choices(ingredients, weights=ingredient_weights)[0]
                    quantity = round(min(max(rng.lognormvariate(0.1, 0.7), 0.1), 12), 3)
                    db.add(
                        models.WasteEntry(
                            restaurant_id=restaurant.id,
                            ingredient_id=ingredient.id,
                            quantity_kg=quantity,
                            # Prices drift a little over time in real life
                            price_per_kg=round(ingredient.price_per_kg * rng.uniform(0.94, 1.06), 2),
                            reason=rng.choices(reason_names, weights=reason_weights)[0],
                            waste_date=day,
                        )
                    )
        db.commit()

        entries = db.scalar(select(func.count(models.WasteEntry.id)))
        print(f"Created {entries} demo waste entries over {DAYS} days for {len(PROFILES)} restaurants.")


if __name__ == "__main__":
    generate()