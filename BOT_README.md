# Max Quest Bot

Реализация зоны ответственности участника 1: бот в MAX, который проводит пользователя по квесту от `/start` до завершения.

## Что уже есть

- регистрация пользователя по `max_user_id`
- согласие на обработку данных
- обязательный запрос телефона через кнопку `request_contact`
- стартовое сообщение с кнопкой `Старт`
- список доступных квестов
- описание квеста и запуск
- последовательная выдача вопросов
- проверка ответа
- подсказка
- показ правильного ответа после сдачи или исчерпания попыток
- финальное сообщение о завершении
- два режима запуска: `polling` и `webhook`

По умолчанию бот работает через общий `SQLite`-backend и использует ту же базу, что и админ-панель. Для локальной отладки по-прежнему можно включить `memory`-режим без общей базы.

## Быстрый старт

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Заполните в `.env`:

```env
MAX_BOT_TOKEN=ваш_токен
BOT_RUN_MODE=polling
BOT_BACKEND=sqlite
BOT_DB_PATH=.local/admin_panel.sqlite3
BOT_REQUIRE_PHONE=true
```

Запуск:

```bash
python main.py
```

Проверка тестов:

```bash
pytest
```

## Режимы работы

### Polling

Подходит для локальной разработки.

```env
BOT_RUN_MODE=polling
```

### Webhook

Подходит для сервера.

```env
BOT_RUN_MODE=webhook
BOT_HOST=0.0.0.0
BOT_PORT=8080
BOT_WEBHOOK_PATH=/webhook
BOT_WEBHOOK_SECRET=секрет_если_нужен
```

Запуск:

```bash
python main.py
```

## Хранилище данных

По умолчанию:

```env
BOT_BACKEND=sqlite
BOT_DB_PATH=.local/admin_panel.sqlite3
```

Это означает, что бот и админ-панель используют один и тот же файл базы данных.

Для локального изолированного режима можно переключиться на память:

```env
BOT_BACKEND=memory
```

Точка интеграции бота с общей системой теперь находится в `max_quest_bot/sqlite_backend.py`.
