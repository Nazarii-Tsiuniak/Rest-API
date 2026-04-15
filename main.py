from flask import Flask, request
from flask_restful import Api, Resource
from flasgger import Swagger, swag_from
from pydantic import ValidationError

from database import connect, get_books_collection
from repository.book_repository import BookRepository
from schemas.book import BookCreate
from services.book_service import BookService


def create_app(repo: BookRepository | None = None) -> Flask:
    app = Flask(__name__)
    Swagger(app)
    api = Api(app)

    connect()
    repository = repo or BookRepository(get_books_collection())
    service = BookService(repository)

    class BooksResource(Resource):
        @swag_from({
            "tags": ["Books"],
            "parameters": [
                {"name": "limit", "in": "query", "type": "integer"},
                {"name": "offset", "in": "query", "type": "integer"},
                {"name": "status", "in": "query", "type": "string"},
                {"name": "author", "in": "query", "type": "string"},
                {"name": "sort_by", "in": "query", "type": "string"},
            ],
            "responses": {200: {"description": "List of books"}},
        })
        def get(self):
            status = request.args.get("status")
            author = request.args.get("author")
            sort_by = request.args.get("sort_by")
            try:
                limit = int(request.args.get("limit", 10))
                offset = int(request.args.get("offset", 0))
            except ValueError:
                return {"detail": "Invalid limit/offset"}, 400
            books = service.get_all_books_by_offset(
                status=status,
                author=author,
                sort_by=sort_by,
                limit=limit,
                offset=offset,
                request_url=request.url,
            )
            return books, 200

        @swag_from({
            "tags": ["Books"],
            "parameters": [
                {
                    "name": "body",
                    "in": "body",
                    "required": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "author": {"type": "string"},
                            "description": {"type": "string"},
                            "year": {"type": "integer"},
                            "status": {"type": "string"},
                        },
                        "required": ["title", "author", "description", "year", "status"],
                    },
                }
            ],
            "responses": {201: {"description": "Created book"}},
        })
        def post(self):
            try:
                book = BookCreate(**(request.json or {}))
            except ValidationError as exc:
                return {"detail": exc.errors()}, 422
            created = service.create_book(book)
            return created, 201

    class BookResource(Resource):
        @swag_from({
            "tags": ["Books"],
            "parameters": [
                {"name": "book_id", "in": "path", "type": "string", "required": True}
            ],
            "responses": {200: {"description": "Book"}},
        })
        def get(self, book_id: str):
            try:
                book = service.get_book(book_id)
            except Exception:
                return {"detail": "Invalid book id"}, 400
            if not book:
                return {"detail": "Book not found"}, 404
            return book, 200

        @swag_from({
            "tags": ["Books"],
            "parameters": [
                {"name": "book_id", "in": "path", "type": "string", "required": True}
            ],
            "responses": {204: {"description": "Deleted"}},
        })
        def delete(self, book_id: str):
            try:
                service.delete_book(book_id)
            except Exception:
                return {"detail": "Invalid book id"}, 400
            return "", 204

    api.add_resource(BooksResource, "/books/")
    api.add_resource(BookResource, "/books/<string:book_id>")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
