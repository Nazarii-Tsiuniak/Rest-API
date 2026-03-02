from typing import List, Dict, Optional
from uuid import UUID
from models.book_storage import books_storage


class BookRepository:

    async def get_all(self) -> List[Dict]:
        return books_storage

    async def get_by_id(self, book_id: UUID) -> Optional[Dict]:
        for book in books_storage:
            if book["id"] == book_id:
                return book
        return None

    async def add(self, book: Dict) -> None:
        books_storage.append(book)

    async def delete(self, book_id: UUID) -> None:
        global books_storage
        books_storage[:] = [
            book for book in books_storage if book["id"] != book_id
        ]