import os

import pytest
from fastapi.testclient import TestClient

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


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def auth_headers(client: TestClient) -> dict:
    token_response = client.post(
        "/auth/token",
        json={"username": "admin", "password": "admin"},
    )
    assert token_response.status_code == 200
    access_token = token_response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


def create_book(client: TestClient, headers: dict, **overrides) -> dict:
    payload = {
        "title": "Test Book",
        "author": "Author",
        "description": "Desc",
        "year": 2024,
        "status": "available",
    }
    payload.update(overrides)
    response = client.post("/books/", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


def test_issue_tokens_success(client: TestClient):
    response = client.post("/auth/token", json={
        "username": "admin",
        "password": "admin",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_issue_tokens_invalid_credentials_returns_401(client: TestClient):
    response = client.post("/auth/token", json={
        "username": "admin",
        "password": "wrong",
    })
    assert response.status_code == 401


def test_issue_tokens_invalid_payload_returns_422(client: TestClient):
    response = client.post("/auth/token", json={"username": "admin"})
    assert response.status_code == 422


def test_refresh_tokens_success(client: TestClient):
    token_response = client.post("/auth/token", json={
        "username": "admin",
        "password": "admin",
    })
    refresh_token = token_response.json()["refresh_token"]
    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_refresh_tokens_invalid_token_returns_401(client: TestClient):
    response = client.post("/auth/refresh", json={"refresh_token": "invalid"})
    assert response.status_code == 401


def test_refresh_tokens_invalid_payload_returns_422(client: TestClient):
    response = client.post("/auth/refresh", json={})
    assert response.status_code == 422


def test_books_requires_auth_returns_401(client: TestClient):
    response = client.get("/books/")
    assert response.status_code == 401


def test_books_with_invalid_auth_returns_401(client: TestClient):
    response = client.get(
        "/books/",
        headers={"Authorization": "Bearer invalid"},
    )
    assert response.status_code == 401


def test_create_and_get_book(client: TestClient):
    headers = auth_headers(client)
    data = create_book(client, headers)
    book_id = data["id"]

    get_response = client.get(f"/books/{book_id}", headers=headers)
    assert get_response.status_code == 200


def test_books_cursor_pagination(client: TestClient):
    headers = auth_headers(client)
    for idx in range(3):
        create_book(client, headers, title=f"Book {idx}", year=2020 + idx)

    response = client.get("/books/?limit=2&sort_by=title", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert len(data["items"]) == 2
    assert data["items"][0]["title"] == "Book 0"
    assert data["items"][1]["title"] == "Book 1"
    assert data["next_cursor"]

    response = client.get(
        f"/books/?limit=2&sort_by=title&cursor={data['next_cursor']}",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Book 2"


def test_get_books_invalid_sort_returns_400(client: TestClient):
    headers = auth_headers(client)
    response = client.get("/books/?sort_by=invalid", headers=headers)
    assert response.status_code == 400


def test_get_books_invalid_cursor_returns_400(client: TestClient):
    headers = auth_headers(client)
    response = client.get("/books/?sort_by=title&cursor=broken", headers=headers)
    assert response.status_code == 400


def test_get_book_not_found_returns_404(client: TestClient):
    headers = auth_headers(client)
    response = client.get("/books/00000000-0000-0000-0000-000000000000", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"


def test_delete_book_idempotent(client: TestClient):
    headers = auth_headers(client)
    response = client.delete(
        "/books/00000000-0000-0000-0000-000000000000",
        headers=headers,
    )
    assert response.status_code == 204


def test_get_book_invalid_uuid_returns_422(client: TestClient):
    headers = auth_headers(client)
    response = client.get("/books/not-a-uuid", headers=headers)
    assert response.status_code == 422


def test_delete_book_invalid_uuid_returns_422(client: TestClient):
    headers = auth_headers(client)
    response = client.delete("/books/not-a-uuid", headers=headers)
    assert response.status_code == 422


def test_create_book_invalid_payload_returns_422(client: TestClient):
    headers = auth_headers(client)
    response = client.post("/books/", json={
        "title": "Bad book",
        "author": "Author",
        "description": "Desc",
        "year": -1,
        "status": "archived",
    }, headers=headers)
    assert response.status_code == 422


@pytest.mark.parametrize("query", ["limit=0", "limit=101"])
def test_get_books_invalid_limit_returns_422(client: TestClient, query: str):
    headers = auth_headers(client)
    response = client.get(f"/books/?{query}", headers=headers)
    assert response.status_code == 422
