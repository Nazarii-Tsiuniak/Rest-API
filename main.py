from fastapi import FastAPI

from api.books import router
from database import Base, SessionLocal, engine
from seed_data import seed_books_if_empty


def startup_tasks() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_books_if_empty(db)


app = FastAPI(title="Library API")


@app.on_event("startup")
def on_startup() -> None:
    startup_tasks()

app.include_router(router)
