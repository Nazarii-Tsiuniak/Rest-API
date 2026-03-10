from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from models.book import Book
from schemas.book import BookCreate


class BookRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_cursor(
        self,
        status: Optional[str] = None,
        author: Optional[str] = None,
        sort_by: Optional[str] = None,
        limit: int = 10,
        cursor: Optional[str] = None,
    ) -> tuple[list[Book], Optional[str]]:
        query = self.db.query(Book)

        if status:
            query = query.filter(Book.status == status)

        if author:
            query = query.filter(Book.author.ilike(author))

        if sort_by is None:
            if cursor:
                if "|" in cursor:
                    raise ValueError("Invalid cursor format for default sort")
                query = query.filter(Book.id > cursor)
            query = query.order_by(Book.id)
        elif sort_by == "title":
            if cursor:
                parts = cursor.split("|", 1)
                if len(parts) != 2:
                    raise ValueError("Invalid cursor format for title sort")
                title_value, id_value = parts
                query = query.filter(
                    or_(
                        Book.title > title_value,
                        and_(Book.title == title_value, Book.id > id_value),
                    )
                )
            query = query.order_by(Book.title, Book.id)
        elif sort_by == "year":
            if cursor:
                parts = cursor.split("|", 1)
                if len(parts) != 2:
                    raise ValueError("Invalid cursor format for year sort")
                year_value, id_value = parts
                if not year_value.isdigit():
                    raise ValueError("Invalid cursor format for year sort")
                query = query.filter(
                    or_(
                        Book.year > int(year_value),
                        and_(Book.year == int(year_value), Book.id > id_value),
                    )
                )
            query = query.order_by(Book.year, Book.id)
        else:
            raise ValueError("Invalid sort_by value")

        items = query.limit(limit + 1).all()
        next_cursor = None
        if len(items) > limit:
            last = items[limit - 1]
            if sort_by is None:
                next_cursor = last.id
            elif sort_by == "title":
                next_cursor = f"{last.title}|{last.id}"
            else:
                next_cursor = f"{last.year}|{last.id}"
            items = items[:limit]

        return items, next_cursor

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
