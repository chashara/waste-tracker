import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db
from .routers import stats, waste


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create the tables on startup if they don't exist yet
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Waste Tracker API", lifespan=lifespan)

# Only the React app's address may call this API from a browser
client_url = os.getenv("CLIENT_URL", "http://localhost:5173").rstrip("/")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[client_url],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(waste.router)
app.include_router(stats.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/restaurants", response_model=list[schemas.RestaurantOut])
def list_restaurants(db: Session = Depends(get_db)):
    return db.scalars(select(models.Restaurant).order_by(models.Restaurant.name)).all()


@app.get("/api/ingredients", response_model=list[schemas.IngredientOut])
def list_ingredients(search: Optional[str] = None, db: Session = Depends(get_db)):
    query = select(models.Ingredient).order_by(models.Ingredient.name)
    if search:
        query = query.where(models.Ingredient.name.ilike(f"%{search}%"))
    return db.scalars(query).all()