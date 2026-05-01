import os

import pytest
from httpx import ASGITransport, AsyncClient

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SEED_DATA"] = "0"

from database import Base, SessionLocal, engine, get_db
from main import app
from services.rate_limiter import get_redis


def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


class FakeRedis:
    def __init__(self):
        self.storage: dict[str, dict[str, int]] = {}

    async def zremrangebyscore(self, key: str, min: int, max: int):
        bucket = self.storage.get(key, {})
        self.storage[key] = {
            member: score for member, score in bucket.items()
            if not (min <= score <= max)
        }

    async def zcard(self, key: str) -> int:
        return len(self.storage.get(key, {}))

    async def zadd(self, key: str, mapping: dict[str, int]):
        bucket = self.storage.setdefault(key, {})
        bucket.update(mapping)

    async def expire(self, key: str, period: int):
        return True


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def override_redis():
    fake_redis = FakeRedis()
    app.dependency_overrides[get_redis] = lambda: fake_redis
    yield
    app.dependency_overrides.pop(get_redis, None)


@pytest.mark.asyncio
async def test_refresh_flow():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        register_response = await ac.post("/auth/register", json={
            "username": "admin",
            "password": "admin",
        })
        assert register_response.status_code == 201

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
