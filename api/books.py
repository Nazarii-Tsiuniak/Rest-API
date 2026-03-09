from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from repository.book_repository import BookRepository
from schemas.book import BookCreate, BookResponse
from services.book_service import BookService

router = APIRouter(prefix="/books", tags=["Books"])


def get_book_service(db: Session = Depends(get_db)) -> BookService:
    return BookService(BookRepository(db))


@router.get("/", response_model=List[BookResponse], status_code=200)
def get_books(
    status: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: BookService = Depends(get_book_service),
):
    return service.get_books(status, author, sort_by, limit, offset)


@router.get("/{book_id}", response_model=BookResponse, status_code=200)
def get_book(book_id: UUID, service: BookService = Depends(get_book_service)):
    book = service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.post("/", response_model=BookResponse, status_code=201)
def create_book(book: BookCreate, service: BookService = Depends(get_book_service)):
    return service.create_book(book)


@router.delete("/{book_id}", status_code=204)
def delete_book(book_id: UUID, service: BookService = Depends(get_book_service)):
    service.delete_book(book_id)
    return
