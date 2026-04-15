import pytest

from main import create_app


class FakeBookRepository:
    def __init__(self):
        self._books: list[dict] = []
        self._counter = 0

    def _validate_object_id(self, book_id: str):
        if len(book_id) != 24:
            raise ValueError("Invalid id")
        int(book_id, 16)

    def get_all(self, status=None, author=None, sort_by=None, limit=10, offset=0):
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

    def get_count(self, status=None, author=None):
        books = self._books[:]
        if status:
            books = [b for b in books if b["status"] == status]
        if author:
            books = [b for b in books if b["author"].lower() == author.lower()]
        return len(books)

    def get_by_id(self, book_id: str):
        self._validate_object_id(book_id)
        for book in self._books:
            if book["id"] == book_id:
                return book
        return None

    def add(self, book):
        self._counter += 1
        book_dict = book.model_dump()
        book_dict["id"] = f"{self._counter:024x}"
        self._books.append(book_dict)
        return book_dict

    def delete(self, book_id: str):
        self._validate_object_id(book_id)
        before = len(self._books)
        self._books = [b for b in self._books if b["id"] != book_id]
        return len(self._books) < before


@pytest.fixture()
def client():
    repo = FakeBookRepository()
    app = create_app(repo)
    app.config["TESTING"] = True
    return app.test_client()


def create_book(client, **overrides):
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
    return response.get_json()


def test_create_and_get_book(client):
    data = create_book(client)
    book_id = data["id"]

    get_response = client.get(f"/books/{book_id}")
    assert get_response.status_code == 200


def test_books_limit_offset_pagination(client):
    for idx in range(3):
        create_book(client, title=f"Book {idx}", year=2020 + idx)

    response = client.get("/books/?limit=2&offset=1&sort_by=title")
    assert response.status_code == 200

    data = response.get_json()
    assert data["count"] == 3
    assert data["offset"] == 1
    assert data["limit"] == 2
    assert data["next"] is None
    assert len(data["results"]) == 2
    assert data["results"][0]["title"] == "Book 1"
    assert data["results"][1]["title"] == "Book 2"


def test_books_pagination_next_link(client):
    for idx in range(4):
        create_book(client, title=f"Book {idx}", year=2020 + idx)

    response = client.get("/books/?limit=2&offset=0")
    assert response.status_code == 200

    data = response.get_json()
    assert data["count"] == 4
    assert data["offset"] == 0
    assert data["limit"] == 2
    assert data["next"] == "http://localhost/books/?limit=2&offset=2"
    assert len(data["results"]) == 2


def test_delete_book_idempotent(client):
    response = client.delete("/books/000000000000000000000000")
    assert response.status_code == 204


def test_get_book_not_found_returns_404(client):
    response = client.get("/books/000000000000000000000000")
    assert response.status_code == 404
    assert response.get_json()["detail"] == "Book not found"


def test_get_book_invalid_id_returns_400(client):
    response = client.get("/books/not-an-object-id")
    assert response.status_code == 400
    assert response.get_json()["detail"] == "Invalid book id"


def test_delete_book_invalid_id_returns_400(client):
    response = client.delete("/books/not-an-object-id")
    assert response.status_code == 400
    assert response.get_json()["detail"] == "Invalid book id"


def test_get_books_invalid_limit_returns_400(client):
    response = client.get("/books/?limit=abc")
    assert response.status_code == 400
    assert response.get_json()["detail"] == "Invalid limit/offset"


def test_get_books_invalid_offset_returns_400(client):
    response = client.get("/books/?offset=abc")
    assert response.status_code == 400
    assert response.get_json()["detail"] == "Invalid limit/offset"


def test_create_book_invalid_payload_returns_422(client):
    response = client.post("/books/", json={
        "title": "Bad book",
        "author": "Author",
        "description": "Desc",
        "year": -1,
        "status": "archived",
    })
    assert response.status_code == 422
