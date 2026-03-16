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
async def test_create_and_get_book():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token_response = await ac.post("/auth/token", json={
            "username": "admin",
            "password": "admin",
        })
        assert token_response.status_code == 200
        access_token = token_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await ac.post("/books/", json={
            "title": "Test Book",
            "author": "Author",
            "description": "Desc",
            "year": 2024,
            "status": "available"
        }, headers=headers)

        assert response.status_code == 201
        data = response.json()
        book_id = data["id"]

        get_response = await ac.get(f"/books/{book_id}", headers=headers)
        assert get_response.status_code == 200


@pytest.mark.asyncio
async def test_books_cursor_pagination():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token_response = await ac.post("/auth/token", json={
            "username": "admin",
            "password": "admin",
        })
        assert token_response.status_code == 200
        access_token = token_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        for idx in range(3):
            await ac.post("/books/", json={
                "title": f"Book {idx}",
                "author": "Author",
                "description": "Desc",
                "year": 2020 + idx,
                "status": "available",
            }, headers=headers)

        response = await ac.get("/books/?limit=2&sort_by=title", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) == 2
        assert data["items"][0]["title"] == "Book 0"
        assert data["items"][1]["title"] == "Book 1"
        assert data["next_cursor"]

        response = await ac.get(
            f"/books/?limit=2&sort_by=title&cursor={data['next_cursor']}",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Book 2"


@pytest.mark.asyncio
async def test_delete_book_idempotent():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        token_response = await ac.post("/auth/token", json={
            "username": "admin",
            "password": "admin",
        })
        assert token_response.status_code == 200
        access_token = token_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        response = await ac.delete(
            "/books/00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        assert response.status_code == 204
