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

### Пагінація (cursor)
Ендпоінт `GET /books/` підтримує параметри:
- `limit` (default: `10`, min: `1`, max: `100`)
- `cursor` (рядок з відповіді `next_cursor`)
- `status`
- `author`
- `sort_by` (`title` або `year`)

Приклад:
```http
GET /books/?limit=5&sort_by=title
```

### Локальний запуск тестів
```bash
pytest
```
