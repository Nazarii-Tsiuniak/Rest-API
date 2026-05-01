from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.auth import router as auth_router
from api.books import router as books_router
from database import Base, SessionLocal, engine
from seed_data import seed_books_if_empty


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_books_if_empty(db)
    yield


app = FastAPI(title="Library API", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(books_router)
