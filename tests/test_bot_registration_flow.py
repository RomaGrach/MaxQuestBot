from __future__ import annotations

from max_quest_bot.config import Settings
from max_quest_bot.keyboards import request_phone_keyboard, start_keyboard


def test_phone_is_required_by_default(monkeypatch) -> None:
    monkeypatch.delenv("BOT_REQUIRE_PHONE", raising=False)
    monkeypatch.setenv("MAX_BOT_TOKEN", "test-token")

    settings = Settings.from_env()

    assert settings.require_phone is True


def test_phone_requirement_can_be_disabled_explicitly(monkeypatch) -> None:
    monkeypatch.setenv("MAX_BOT_TOKEN", "test-token")
    monkeypatch.setenv("BOT_REQUIRE_PHONE", "false")

    settings = Settings.from_env()

    assert settings.require_phone is False


def test_start_keyboard_contains_start_button() -> None:
    markup = start_keyboard()

    assert markup.payload.buttons[0][0].text == "Старт"
    assert markup.payload.buttons[0][0].payload == "nav:start"


def test_required_phone_keyboard_has_no_skip_button() -> None:
    markup = request_phone_keyboard(allow_skip=False)

    assert len(markup.payload.buttons) == 1
    assert markup.payload.buttons[0][0].text == "Поделиться телефоном"
