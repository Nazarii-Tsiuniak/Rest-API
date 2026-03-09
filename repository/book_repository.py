from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from models.book import Book
from schemas.book import BookCreate


class BookRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(
        self,
        status: Optional[str] = None,
        author: Optional[str] = None,
        sort_by: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[Book]:
        query = self.db.query(Book)

        if status:
            query = query.filter(Book.status == status)

        if author:
            query = query.filter(Book.author.ilike(author))

        if sort_by == "title":
            query = query.order_by(Book.title)
        elif sort_by == "year":
            query = query.order_by(Book.year)

        return query.offset(offset).limit(limit).all()

    def get_by_id(self, book_id: UUID) -> Optional[Book]:
        return self.db.query(Book).filter(Book.id == str(book_id)).first()

    def add(self, book: BookCreate) -> Book:
        db_book = Book(id=str(uuid4()), **book.model_dump())
        self.db.add(db_book)
        self.db.commit()
        self.db.refresh(db_book)
        return db_book

    def delete(self, book_id: UUID) -> None:
        db_book = self.get_by_id(book_id)
        if db_book is None:
            return

        self.db.delete(db_book)
        self.db.commit()
