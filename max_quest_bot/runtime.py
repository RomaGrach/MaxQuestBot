from __future__ import annotations

import logging

from maxapi import Bot, Dispatcher
from maxapi.types.command import BotCommand
from maxapi.webhook.fastapi import FastAPIMaxWebhook

from max_quest_bot.backend import InMemoryQuestBackend
from max_quest_bot.config import Settings
from max_quest_bot.handlers import register_handlers
from max_quest_bot.sqlite_backend import SQLiteQuestBackend, SqliteBackendSettings


def build_bot_commands() -> tuple[BotCommand, ...]:
    return (
        BotCommand(name="start", description="Начать или продолжить сценарий"),
        BotCommand(name="quests", description="Показать доступные квесты"),
        BotCommand(name="status", description="Показать текущий статус"),
        BotCommand(name="info", description="Краткая информация о боте"),
        BotCommand(name="help", description="Справка по командам"),
    )


def create_dispatcher(settings: Settings) -> tuple[Bot, Dispatcher]:
    bot = Bot(token=settings.max_bot_token)
    dp = Dispatcher()
    if settings.backend_mode == "memory":
        backend = InMemoryQuestBackend()
    else:
        backend = SQLiteQuestBackend(
            SqliteBackendSettings(db_path=settings.db_path)
        )
    register_handlers(dp=dp, settings=settings, backend=backend)
    return bot, dp


async def run_bot() -> None:
    settings = Settings.from_env()
    settings.validate()
    logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO))

    bot, dp = create_dispatcher(settings)
    try:
        await bot.set_my_commands(*build_bot_commands())
    except Exception:  # pragma: no cover - defensive only
        logging.warning("Failed to sync bot commands.", exc_info=True)
    if settings.run_mode == "polling":
        await bot.delete_webhook()
        await dp.start_polling(bot)
        return

    webhook = FastAPIMaxWebhook(
        dp=dp,
        bot=bot,
        secret=settings.webhook_secret,
    )
    await webhook.run(
        host=settings.host,
        port=settings.port,
        path=settings.webhook_path,
    )
