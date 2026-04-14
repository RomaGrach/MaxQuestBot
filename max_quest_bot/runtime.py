from __future__ import annotations

import logging

from maxapi import Bot, Dispatcher
from maxapi.webhook.fastapi import FastAPIMaxWebhook

from max_quest_bot.backend import InMemoryQuestBackend
from max_quest_bot.config import Settings
from max_quest_bot.handlers import register_handlers


def create_dispatcher(settings: Settings) -> tuple[Bot, Dispatcher]:
    bot = Bot(token=settings.max_bot_token)
    dp = Dispatcher()
    backend = InMemoryQuestBackend()
    register_handlers(dp=dp, settings=settings, backend=backend)
    return bot, dp


async def run_bot() -> None:
    settings = Settings.from_env()
    settings.validate()
    logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO))

    bot, dp = create_dispatcher(settings)
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

