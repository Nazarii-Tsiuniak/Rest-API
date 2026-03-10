import os
from uuid import NAMESPACE_DNS, uuid5

from sqlalchemy.orm import Session

from models.book import Book


def _seed_enabled() -> bool:
    return os.getenv("SEED_DATA", "1").lower() not in {"0", "false", "no"}


def seed_books_if_empty(db: Session) -> None:
    if not _seed_enabled():
        return

    books = []
    for idx in range(1, 31):
        seed_key = f"seed-{idx:02d}"
        seed_uuid = str(uuid5(NAMESPACE_DNS, seed_key))
        books.append(
            {
                "seed_key": seed_key,
                "id": seed_uuid,
                "title": f"Book {idx:02d}",
                "author": f"Author {((idx - 1) % 6) + 1}",
                "description": f"Seeded book #{idx}",
                "year": 2000 + (idx % 20),
                "status": "available" if idx % 3 else "borrowed",
            }
        )

    existing_ids = {
        row[0] for row in db.query(Book.id).filter(
            Book.id.in_([b["id"] for b in books])
        )
    }

    for book in books:
        if book["id"] in existing_ids:
            continue

        legacy = db.query(Book).filter(Book.id == book["seed_key"]).first()
        if legacy is not None:
            legacy.id = book["id"]
            continue

        db.add(Book(**{k: v for k, v in book.items() if k != "seed_key"}))

    db.commit()
