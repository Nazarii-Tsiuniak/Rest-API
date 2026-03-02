from uuid import uuid4, UUID
from typing import List, Optional
from repository.book_repository import BookRepository
from schemas.book import BookCreate


class BookService:

    def __init__(self):
        self.repository = BookRepository()

    async def get_books(
        self,
        status: Optional[str] = None,
        author: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> List[dict]:

        books = await self.repository.get_all()

        if status:
            books = [b for b in books if b["status"] == status]

        if author:
            books = [b for b in books if b["author"].lower() == author.lower()]

        if sort_by == "title":
            books = sorted(books, key=lambda x: x["title"])
        elif sort_by == "year":
            books = sorted(books, key=lambda x: x["year"])

        return books

    async def get_book(self, book_id: UUID):
        return await self.repository.get_by_id(book_id)

    async def create_book(self, book: BookCreate):
        book_dict = book.dict()
        book_dict["id"] = uuid4()
        await self.repository.add(book_dict)
        return book_dict

    async def delete_book(self, book_id: UUID):
        await self.repository.delete(book_id)