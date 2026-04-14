from __future__ import annotations

from maxapi.types import CallbackButton, RequestContactButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

from max_quest_bot.models import Quest


def start_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(CallbackButton(text="Старт", payload="nav:start"))
    return keyboard.as_markup()


def consent_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        CallbackButton(text="Согласен", payload="consent:accept"),
        CallbackButton(text="Не согласен", payload="consent:decline"),
    )
    return keyboard.as_markup()


def request_phone_keyboard(*, allow_skip: bool = True):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(RequestContactButton(text="Поделиться телефоном"))
    if allow_skip:
        keyboard.row(CallbackButton(text="Пропустить пока", payload="nav:quests"))
    return keyboard.as_markup()


def quests_keyboard(quests: list[Quest]):
    keyboard = InlineKeyboardBuilder()
    for quest in quests:
        keyboard.row(
            CallbackButton(text=quest.title, payload=f"quest:open:{quest.id}")
        )
    return keyboard.as_markup()


def quest_card_keyboard(quest_id: str):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(CallbackButton(text="Начать квест", payload=f"quest:start:{quest_id}"))
    keyboard.row(CallbackButton(text="К списку квестов", payload="nav:quests"))
    return keyboard.as_markup()


def active_question_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        CallbackButton(text="Подсказка", payload="quest:hint"),
        CallbackButton(text="Сдаться", payload="quest:giveup"),
    )
    keyboard.row(CallbackButton(text="Что умеет бот", payload="nav:help"))
    return keyboard.as_markup()


def help_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        CallbackButton(text="Квесты", payload="nav:quests"),
        CallbackButton(text="Статус", payload="nav:status"),
    )
    keyboard.row(CallbackButton(text="Инфо", payload="nav:info"))
    return keyboard.as_markup()
