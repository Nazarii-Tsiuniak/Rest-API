import pytest
from httpx import ASGITransport, AsyncClient

from api.books import get_book_service
from main import app
from services.book_service import BookService


class FakeBookRepository:
    def __init__(self):
        self._books: list[dict] = []
        self._counter = 0

    async def get_all(
        self,
        status=None,
        author=None,
        sort_by=None,
        limit=10,
        offset=0,
    ):
        books = self._books[:]
        if status:
            books = [b for b in books if b["status"] == status]
        if author:
            books = [b for b in books if b["author"].lower() == author.lower()]
        if sort_by == "title":
            books = sorted(books, key=lambda x: x["title"])
        elif sort_by == "year":
            books = sorted(books, key=lambda x: x["year"])
        return books[offset: offset + limit]

    async def get_by_id(self, book_id: str):
        for book in self._books:
            if str(book["id"]) == book_id:
                return book
        return None

    async def add(self, book):
        book_dict = book.model_dump()
        self._counter += 1
        book_dict["id"] = f"{self._counter:024x}"
        self._books.append(book_dict)
        return book_dict

    async def delete(self, book_id: str):
        before = len(self._books)
        self._books = [b for b in self._books if str(b["id"]) != book_id]
        return len(self._books) < before


fake_repo = FakeBookRepository()


def override_get_service():
    return BookService(fake_repo)


app.dependency_overrides[get_book_service] = override_get_service


@pytest.fixture(autouse=True)
def reset_repo():
    fake_repo._books = []
    yield


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
async def test_books_limit_offset_pagination():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for idx in range(3):
            await ac.post("/books/", json={
                "title": f"Book {idx}",
                "author": "Author",
                "description": "Desc",
                "year": 2020 + idx,
                "status": "available",
            })

        response = await ac.get("/books/?limit=2&offset=1&sort_by=title")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "Book 1"
        assert data[1]["title"] == "Book 2"


@pytest.mark.asyncio
async def test_delete_book_idempotent():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.delete("/books/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 204
