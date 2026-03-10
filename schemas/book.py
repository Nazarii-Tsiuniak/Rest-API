from pydantic import BaseModel, ConfigDict, Field
from pydantic_mongo import PydanticObjectId
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
    model_config = ConfigDict(from_attributes=True)

    id: PydanticObjectId
