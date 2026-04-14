from __future__ import annotations

from max_quest_bot.keyboards import help_keyboard
from max_quest_bot.runtime import build_bot_commands


def test_help_keyboard_contains_navigation_buttons() -> None:
    markup = help_keyboard()

    assert markup.payload.buttons[0][0].text == "Квесты"
    assert markup.payload.buttons[0][0].payload == "nav:quests"
    assert markup.payload.buttons[0][1].text == "Статус"
    assert markup.payload.buttons[0][1].payload == "nav:status"
    assert markup.payload.buttons[1][0].text == "Инфо"
    assert markup.payload.buttons[1][0].payload == "nav:info"


def test_build_bot_commands_exposes_navigation_commands() -> None:
    commands = build_bot_commands()

    assert [command.name for command in commands] == [
        "start",
        "quests",
        "status",
        "info",
        "help",
    ]
