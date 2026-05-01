import os

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SEED_DATA"] = "0"

from database import Base, SessionLocal, engine, get_db
from main import app
from services.rate_limiter import get_redis


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


@pytest.fixture(autouse=True)
def override_redis():
    fake_redis = FakeRedis()
    app.dependency_overrides[get_redis] = lambda: fake_redis
    yield
    app.dependency_overrides.pop(get_redis, None)


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def auth_headers(client: TestClient) -> dict:
    register_response = client.post(
        "/auth/register",
        json={"username": "admin", "password": "admin"},
    )
    assert register_response.status_code == 201

    token_response = client.post(
        "/auth/token",
        json={"username": "admin", "password": "admin"},
    )
    assert token_response.status_code == 200
    access_token = token_response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def test_anonymous_under_limit_returns_200(client: TestClient):
    register_response = client.post(
        "/auth/register",
        json={"username": "admin", "password": "admin"},
    )
    assert register_response.status_code == 201

    first = client.post("/auth/token", json={"username": "admin", "password": "admin"})
    second = client.post("/auth/token", json={"username": "admin", "password": "admin"})

    assert first.status_code == 200
    assert second.status_code == 200


def test_anonymous_reaches_limit_returns_429(client: TestClient):
    register_response = client.post(
        "/auth/register",
        json={"username": "admin", "password": "admin"},
    )
    assert register_response.status_code == 201

    client.post("/auth/token", json={"username": "admin", "password": "admin"})
    client.post("/auth/token", json={"username": "admin", "password": "admin"})
    third = client.post("/auth/token", json={"username": "admin", "password": "admin"})

    assert third.status_code == 429


def test_authenticated_under_limit_returns_200(client: TestClient):
    headers = auth_headers(client)

    responses = [client.get("/books/", headers=headers) for _ in range(10)]
    assert all(response.status_code == 200 for response in responses)


def test_authenticated_reaches_limit_returns_429(client: TestClient):
    headers = auth_headers(client)

    for _ in range(10):
        client.get("/books/", headers=headers)
    limit_hit = client.get("/books/", headers=headers)

    assert limit_hit.status_code == 429
