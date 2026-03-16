import os

import pytest
from httpx import ASGITransport, AsyncClient

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SEED_DATA"] = "0"

from database import Base, SessionLocal, engine, get_db
from main import app


def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.mark.asyncio
async def test_refresh_flow():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token_response = await ac.post("/auth/token", json={
            "username": "admin",
            "password": "admin",
        })
        assert token_response.status_code == 200
        refresh_token = token_response.json()["refresh_token"]

        refresh_response = await ac.post("/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert refresh_response.status_code == 200
        data = refresh_response.json()
        assert data["access_token"]
        assert data["refresh_token"]
