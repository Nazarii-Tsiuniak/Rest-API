import pytest

from main import create_app


class FakeBookRepository:
    def __init__(self):
        self._books: list[dict] = []
        self._counter = 0

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

    def get_by_id(self, book_id: str):
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
        before = len(self._books)
        self._books = [b for b in self._books if b["id"] != book_id]
        return len(self._books) < before


@pytest.fixture()
def client():
    repo = FakeBookRepository()
    app = create_app(repo)
    app.config["TESTING"] = True
    return app.test_client()


def test_create_and_get_book(client):
    response = client.post("/books/", json={
        "title": "Test Book",
        "author": "Author",
        "description": "Desc",
        "year": 2024,
        "status": "available",
    })
    assert response.status_code == 201
    data = response.get_json()
    book_id = data["id"]

    get_response = client.get(f"/books/{book_id}")
    assert get_response.status_code == 200


def test_books_limit_offset_pagination(client):
    for idx in range(3):
        client.post("/books/", json={
            "title": f"Book {idx}",
            "author": "Author",
            "description": "Desc",
            "year": 2020 + idx,
            "status": "available",
        })

    response = client.get("/books/?limit=2&offset=1&sort_by=title")
    assert response.status_code == 200

    data = response.get_json()
    assert len(data) == 2
    assert data[0]["title"] == "Book 1"
    assert data[1]["title"] == "Book 2"


def test_delete_book_idempotent(client):
    response = client.delete("/books/000000000000000000000000")
    assert response.status_code == 204
