import os
from uuid import uuid4

from sqlalchemy.orm import Session

from models.book import Book


def _seed_enabled() -> bool:
    return os.getenv("SEED_DATA", "0").lower() in {"1", "true", "yes"}


def seed_books_if_empty(db: Session) -> None:
    if not _seed_enabled():
        return

    if db.query(Book).first() is not None:
        return

    books = []
    for idx in range(1, 31):
        books.append(
            Book(
                id=str(uuid4()),
                title=f"Book {idx:02d}",
                author=f"Author {((idx - 1) % 6) + 1}",
                description=f"Seeded book #{idx}",
                year=2000 + (idx % 20),
                status="available" if idx % 3 else "borrowed",
            )
        )

    db.add_all(books)
    db.commit()
