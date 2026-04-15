from typing import Optional

from bson import ObjectId
from pymongo.collection import Collection

from schemas.book import BookCreate


class BookRepository:
    def __init__(self, collection: Collection):
        self.collection = collection

    def _normalize(self, doc: dict) -> dict:
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return doc

    def _build_query(
        self,
        status: Optional[str] = None,
        author: Optional[str] = None,
    ) -> dict:
        query: dict = {}

        if status:
            query["status"] = status

        if author:
            query["author"] = {"$regex": f"^{author}$", "$options": "i"}

        return query

    def get_all(
        self,
        status: Optional[str] = None,
        author: Optional[str] = None,
        sort_by: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[dict]:
        query = self._build_query(status=status, author=author)

        cursor = self.collection.find(query)

        if sort_by == "title":
            cursor = cursor.sort("title", 1)
        elif sort_by == "year":
            cursor = cursor.sort("year", 1)

        cursor = cursor.skip(offset).limit(limit)
        return [self._normalize(d) for d in list(cursor)]

    def get_count(
        self,
        status: Optional[str] = None,
        author: Optional[str] = None,
    ) -> int:
        query = self._build_query(status=status, author=author)
        return self.collection.count_documents(query)

    def get_by_id(self, book_id: str) -> Optional[dict]:
        doc = self.collection.find_one({"_id": ObjectId(book_id)})
        if doc is None:
            return None
        return self._normalize(doc)

    def add(self, book: BookCreate) -> dict:
        payload = book.model_dump()
        result = self.collection.insert_one(payload)
        return self._normalize({**payload, "_id": result.inserted_id})

    def delete(self, book_id: str) -> bool:
        response = self.collection.delete_one({"_id": ObjectId(book_id)})
        return response.deleted_count > 0
