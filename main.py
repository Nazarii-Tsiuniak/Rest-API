from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.auth import router as auth_router
from api.books import router as books_router
from database import Base, SessionLocal, engine
from models import book as _book  # noqa: F401
from models import user as _user  # noqa: F401
from seed_data import seed_books_if_empty
from services.auth_service import ensure_default_user


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_books_if_empty(db)
        ensure_default_user(db)
    yield


app = FastAPI(title="Library API", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(books_router)
