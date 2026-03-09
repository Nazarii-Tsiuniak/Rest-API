## Library API (Lab 2)

### Stack
- FastAPI
- PostgreSQL
- SQLAlchemy
- Docker / Docker Compose
- Pytest

### Запуск у Docker
```bash
docker compose up --build
```

API буде доступне на `http://localhost:8000`.

### Пагінація (limit-offset)
Ендпоінт `GET /books/` підтримує параметри:
- `limit` (default: `10`, min: `1`, max: `100`)
- `offset` (default: `0`, min: `0`)
- `status`
- `author`
- `sort_by` (`title` або `year`)

Приклад:
```http
GET /books/?limit=5&offset=10&sort_by=title
```

### Локальний запуск тестів
```bash
pytest
```
