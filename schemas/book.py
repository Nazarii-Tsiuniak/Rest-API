from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class PaginationResponse(BaseModel):
    count: int
    offset: int
    limit: int
    next: str | None
    results: list[BookResponse]
