# Lab 9 - Locust Load Testing

## Що реалізовано
- `locustfile.py` для навантажувального тесту ендпоінта `GET /books/`.
- Токен отримується автоматично в `on_start` через `POST /auth/token`.
- Для lab9 у Docker змінною `RATE_LIMIT_ENABLED=0` вимкнено обмеження rate limit.
- У `docker-compose.yml` додано сервіс `locust` (UI на `http://127.0.0.1:8089`).

## Як запустити
```powershell
docker compose -f docker-compose.yml up --build
```

Після старту:
- API: `http://127.0.0.1:8000/docs`
- Locust UI: `http://127.0.0.1:8089`
