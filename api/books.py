from fastapi import APIRouter, HTTPException, Query
from uuid import UUID
from typing import List, Optional
from schemas.book import BookCreate, BookResponse
from services.book_service import BookService

router = APIRouter(prefix="/books", tags=["Books"])
service = BookService()


@router.get("/", response_model=List[BookResponse], status_code=200)
async def get_books(
    status: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None)
):
    return await service.get_books(status, author, sort_by)


@router.get("/{book_id}", response_model=BookResponse, status_code=200)
async def get_book(book_id: UUID):
    book = await service.get_book(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.post("/", response_model=BookResponse, status_code=201)
async def create_book(book: BookCreate):
    return await service.create_book(book)


@router.delete("/{book_id}", status_code=204)
async def delete_book(book_id: UUID):
    await service.delete_book(book_id)
    return