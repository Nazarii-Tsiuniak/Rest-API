from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from database import get_books_collection
from repository.book_repository import BookRepository
from schemas.book import BookCreate, BookResponse
from services.book_service import BookService

router = APIRouter(prefix="/books", tags=["Books"])


def get_book_service(collection=Depends(get_books_collection)) -> BookService:
    return BookService(BookRepository(collection))


@router.get("/", response_model=List[BookResponse], status_code=200)
async def get_books(
    status: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: BookService = Depends(get_book_service),
):
    return await service.get_books(status, author, sort_by, limit, offset)


@router.get("/{book_id}", response_model=BookResponse, status_code=200)
async def get_book(book_id: str, service: BookService = Depends(get_book_service)):
    book = await service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.post("/", response_model=BookResponse, status_code=201)
async def create_book(
    book: BookCreate,
    service: BookService = Depends(get_book_service),
):
    return await service.create_book(book)


@router.delete("/{book_id}", status_code=204)
async def delete_book(book_id: str, service: BookService = Depends(get_book_service)):
    await service.delete_book(book_id)
    return
