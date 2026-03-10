import os

from motor.motor_asyncio import AsyncIOMotorClient

_client: AsyncIOMotorClient | None = None


def _mongo_url() -> str:
    return os.getenv(
        "MONGO_URL",
        "mongodb://mongo_admin:password@mongo:27017",
    )


def _mongo_db() -> str:
    return os.getenv("MONGO_DB", "library")


def _mongo_collection() -> str:
    return os.getenv("MONGO_COLLECTION", "books")


def connect() -> None:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(_mongo_url())


def get_books_collection():
    if _client is None:
        connect()
    return _client[_mongo_db()][_mongo_collection()]


def close() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
