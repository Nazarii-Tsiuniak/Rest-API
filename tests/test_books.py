import pytest
from fastapi.testclient import TestClient

from api.books import get_book_service
from main import app
from services.book_service import BookService


class FakeBookRepository:
    def __init__(self):
        self._books: list[dict] = []
        self._counter = 0

    def _validate_object_id(self, book_id: str) -> None:
        if len(book_id) != 24:
            raise ValueError("Invalid book id")
        int(book_id, 16)

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
        self._validate_object_id(book_id)
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
        self._validate_object_id(book_id)
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
    fake_repo._counter = 0
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


def test_books_limit_offset_pagination(client: TestClient):
    for idx in range(3):
        create_book(client, title=f"Book {idx}", year=2020 + idx)

    response = client.get("/books/?limit=2&offset=1&sort_by=title")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Book 1"
    assert data[1]["title"] == "Book 2"


def test_get_book_not_found_returns_404(client: TestClient):
    response = client.get("/books/000000000000000000000000")
    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"


def test_get_book_invalid_id_returns_400(client: TestClient):
    response = client.get("/books/not-an-object-id")
    assert response.status_code == 400


def test_delete_book_invalid_id_returns_400(client: TestClient):
    response = client.delete("/books/not-an-object-id")
    assert response.status_code == 400


def test_delete_book_idempotent(client: TestClient):
    response = client.delete("/books/000000000000000000000000")
    assert response.status_code == 204


def test_create_book_missing_required_field_returns_422(client: TestClient):
    response = client.post("/books/", json={
        "title": "Missing status",
        "author": "Author",
        "description": "Desc",
        "year": 2024,
    })
    assert response.status_code == 422


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1"])
def test_get_books_invalid_pagination_returns_422(client: TestClient, query: str):
    response = client.get(f"/books/?{query}")
    assert response.status_code == 422
