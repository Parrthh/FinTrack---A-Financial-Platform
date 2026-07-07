import os

os.environ.setdefault("DATABASE_URL", "sqlite://")  # in-memory
os.environ.setdefault("JWT_SECRET", "test-secret-0123456789abcdef0123456789abcdef")
os.environ.setdefault("AUTH_RATE_LIMIT_ATTEMPTS", "100")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture()
def signup_payload():
    return {
        "email": "parth@example.com",
        "password": "correct-horse-battery",
        "display_name": "Parth",
    }
