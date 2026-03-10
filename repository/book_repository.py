from typing import Optional

from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic_mongo import PydanticObjectId

from schemas.book import BookCreate


class BookRepository:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection
        self._id_field = "_id"

    def _normalize(self, doc: dict) -> dict:
        if self._id_field in doc:
            doc["id"] = doc.pop(self._id_field)
        return doc

    async def get_all(
        self,
        status: Optional[str] = None,
        author: Optional[str] = None,
        sort_by: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[dict]:
        query: dict = {}

        if status:
            query["status"] = status

        if author:
            query["author"] = {"$regex": f"^{author}$", "$options": "i"}

        cursor = self.collection.find(query)

        if sort_by == "title":
            cursor = cursor.sort("title", 1)
        elif sort_by == "year":
            cursor = cursor.sort("year", 1)

        cursor = cursor.skip(offset).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self._normalize(d) for d in docs]

    async def get_by_id(self, book_id: str) -> Optional[dict]:
        doc = await self.collection.find_one(
            {"_id": PydanticObjectId(book_id)}
        )
        if doc is None:
            return None
        return self._normalize(doc)

    async def add(self, book: BookCreate) -> dict:
        payload = book.model_dump()
        result = await self.collection.insert_one(payload)
        return {**payload, "id": result.inserted_id}

    async def delete(self, book_id: str) -> bool:
        response = await self.collection.delete_one(
            {"_id": PydanticObjectId(book_id)}
        )
        return response.deleted_count > 0
