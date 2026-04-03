import os

import pytest
from fastapi.testclient import TestClient

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


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def create_book(client: TestClient, **overrides) -> dict:
    payload = {
        "title": "Test Book",
        "author": "Author",
        "description": "Desc",
        "year": 2024,
        "status": "available",
    }
    payload.update(overrides)
    response = client.post("/books/", json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_and_get_book(client: TestClient):
    data = create_book(client)
    book_id = data["id"]

    get_response = client.get(f"/books/{book_id}")
    assert get_response.status_code == 200


def test_books_cursor_pagination(client: TestClient):
    for idx in range(3):
        create_book(client, title=f"Book {idx}", year=2020 + idx)

    response = client.get("/books/?limit=2&sort_by=title")
    assert response.status_code == 200

    data = response.json()
    assert len(data["items"]) == 2
    assert data["items"][0]["title"] == "Book 0"
    assert data["items"][1]["title"] == "Book 1"
    assert data["next_cursor"]

    response = client.get(f"/books/?limit=2&sort_by=title&cursor={data['next_cursor']}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Book 2"


def test_get_book_not_found_returns_404(client: TestClient):
    response = client.get("/books/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"


def test_delete_book_idempotent(client: TestClient):
    response = client.delete("/books/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 204


def test_get_books_invalid_sort_returns_400(client: TestClient):
    response = client.get("/books/?sort_by=invalid")
    assert response.status_code == 400


def test_get_books_invalid_cursor_for_title_returns_400(client: TestClient):
    response = client.get("/books/?sort_by=title&cursor=broken-cursor")
    assert response.status_code == 400


def test_get_books_invalid_cursor_for_year_returns_400(client: TestClient):
    response = client.get("/books/?sort_by=year&cursor=wrong|cursor")
    assert response.status_code == 400


def test_get_book_invalid_uuid_returns_422(client: TestClient):
    response = client.get("/books/not-a-uuid")
    assert response.status_code == 422


def test_delete_book_invalid_uuid_returns_422(client: TestClient):
    response = client.delete("/books/not-a-uuid")
    assert response.status_code == 422


def test_create_book_missing_required_field_returns_422(client: TestClient):
    response = client.post("/books/", json={
        "title": "Missing status",
        "author": "Author",
        "description": "Desc",
        "year": 2024,
    })
    assert response.status_code == 422


@pytest.mark.parametrize("query", ["limit=0", "limit=101"])
def test_get_books_invalid_limit_returns_422(client: TestClient, query: str):
    response = client.get(f"/books/?{query}")
    assert response.status_code == 422
