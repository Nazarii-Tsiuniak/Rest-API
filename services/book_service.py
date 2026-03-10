from typing import Optional
from repository.book_repository import BookRepository
from schemas.book import BookCreate


class BookService:

    def __init__(self, repository: BookRepository):
        self.repository = repository

    async def get_books(
        self,
        status: Optional[str] = None,
        author: Optional[str] = None,
        sort_by: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ):
        return await self.repository.get_all(
            status=status,
            author=author,
            sort_by=sort_by,
            limit=limit,
            offset=offset,
        )

    async def get_book(self, book_id: str):
        return await self.repository.get_by_id(book_id)

    async def create_book(self, book: BookCreate):
        return await self.repository.add(book)

    async def delete_book(self, book_id: str):
        return await self.repository.delete(book_id)
