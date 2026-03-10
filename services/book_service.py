from typing import Optional
from uuid import UUID

from repository.book_repository import BookRepository
from schemas.book import BookCreate


class BookService:

    def __init__(self, repository: BookRepository):
        self.repository = repository

    def get_books(
        self,
        status: Optional[str] = None,
        author: Optional[str] = None,
        sort_by: Optional[str] = None,
        limit: int = 10,
        cursor: Optional[str] = None,
    ):
        return self.repository.get_all_cursor(
            status=status,
            author=author,
            sort_by=sort_by,
            limit=limit,
            cursor=cursor,
        )

    def get_book(self, book_id: UUID):
        return self.repository.get_by_id(book_id)

    def create_book(self, book: BookCreate):
        return self.repository.add(book)

    def delete_book(self, book_id: UUID):
        self.repository.delete(book_id)
