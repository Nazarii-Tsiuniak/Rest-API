from pydantic import BaseModel, Field
from enum import Enum


class BookStatus(str, Enum):
    available = "available"
    borrowed = "borrowed"


class BookBase(BaseModel):
    title: str = Field(min_length=1)
    author: str = Field(min_length=1)
    description: str = Field(min_length=1)
    year: int = Field(ge=0)
    status: BookStatus


class BookCreate(BookBase):
    pass


class BookResponse(BookBase):
    id: str


class PaginationResponse(BaseModel):
    count: int
    offset: int
    limit: int
    next: str | None
    results: list[BookResponse]
