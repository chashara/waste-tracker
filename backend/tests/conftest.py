import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()

    session.add_all(
        [
            models.Restaurant(id=1, name="Test Restaurant"),
            models.Restaurant(id=2, name="Second Restaurant"),
            models.Ingredient(id=1, name="Salmon", category="Fish", price_per_kg=18.0, grams_per_piece=None),
            models.Ingredient(id=2, name="Eggs", category="Dairy", price_per_kg=4.0, grams_per_piece=60),
        ]
    )
    session.commit()

    yield session

    session.close()
    engine.dispose()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    # No "with" block: that would run the startup code against the real database
    yield TestClient(app)
    app.dependency_overrides.clear()