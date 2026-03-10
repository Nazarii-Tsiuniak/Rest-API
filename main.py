from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.books import router
from database import close, connect


@asynccontextmanager
async def lifespan(_: FastAPI):
    connect()
    yield
    close()


app = FastAPI(title="Library API", lifespan=lifespan)

app.include_router(router)
