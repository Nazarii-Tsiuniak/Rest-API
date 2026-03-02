import pytest
from httpx import AsyncClient, ASGITransport
from main import app


@pytest.mark.asyncio
async def test_create_and_get_book():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:

        response = await ac.post("/books/", json={
            "title": "Test Book",
            "author": "Author",
            "description": "Desc",
            "year": 2024,
            "status": "available"
        })

        assert response.status_code == 201
        data = response.json()
        book_id = data["id"]

        get_response = await ac.get(f"/books/{book_id}")
        assert get_response.status_code == 200


@pytest.mark.asyncio
async def test_delete_book_idempotent():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:

        response = await ac.delete("/books/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 204