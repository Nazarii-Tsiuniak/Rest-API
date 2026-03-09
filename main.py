from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.books import router
from database import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Library API", lifespan=lifespan)

app.include_router(router)
