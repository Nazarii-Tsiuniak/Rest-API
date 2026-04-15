from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from repository.book_repository import BookRepository
from schemas.book import BookCreate, PaginationResponse


class BookService:

    def __init__(self, repository: BookRepository):
        self.repository = repository

    def get_all_books_by_offset(
        self,
        status: Optional[str] = None,
        author: Optional[str] = None,
        sort_by: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        request_url: str = "",
    ):
        books = self.repository.get_all(
            status=status,
            author=author,
            sort_by=sort_by,
            limit=limit,
            offset=offset,
        )
        count = self.repository.get_count(status=status, author=author)
        next_url = None

        if offset + limit < count and request_url:
            next_offset = offset + limit
            parsed = urlsplit(request_url)
            query_params = dict(parse_qsl(parsed.query, keep_blank_values=True))
            query_params["offset"] = str(next_offset)
            query_params["limit"] = str(limit)
            next_url = urlunsplit(
                (
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    urlencode(query_params),
                    parsed.fragment,
                )
            )

        return PaginationResponse(
            count=count,
            offset=offset,
            limit=limit,
            next=next_url,
            results=books,
        ).model_dump()

    def get_book(self, book_id: str):
        return self.repository.get_by_id(book_id)

    def create_book(self, book: BookCreate):
        return self.repository.add(book)

    def delete_book(self, book_id: str):
        return self.repository.delete(book_id)
