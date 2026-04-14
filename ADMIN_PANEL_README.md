# Admin Panel MVP

Админ-панель запускается отдельно от бота и использует локальную SQLite-базу.

## Локальный запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Секреты и серверные настройки храните только в `.env.local`.

Минимально нужны:

```env
ADMIN_PANEL_SECRET_KEY=change-me
ADMIN_PANEL_BOOTSTRAP_USERNAME=admin
ADMIN_PANEL_BOOTSTRAP_PASSWORD=change-me-too
```

Запуск:

```bash
python -m admin_panel.main
```

По умолчанию панель слушает `127.0.0.1:8081`.

## Что хранится локально

- `MAX_BOT_TOKEN`
- `ADMIN_PANEL_SECRET_KEY`
- `ADMIN_PANEL_BOOTSTRAP_PASSWORD`
- любые production-URL и прочие серверные секреты

Эти значения не должны попадать в git.

## Проверка

```bash
pytest
```
