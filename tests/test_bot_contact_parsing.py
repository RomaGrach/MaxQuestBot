from __future__ import annotations

from types import SimpleNamespace

from max_quest_bot.handlers import extract_phone_from_message


def test_extract_phone_from_message_returns_phone() -> None:
    message = SimpleNamespace(
        body=SimpleNamespace(
            attachments=[
                SimpleNamespace(
                    type="contact",
                    payload=SimpleNamespace(
                        vcf=SimpleNamespace(phone="+79991234567")
                    ),
                )
            ]
        )
    )

    assert extract_phone_from_message(message) == "+79991234567"


def test_extract_phone_from_message_returns_none_without_contact() -> None:
    message = SimpleNamespace(body=SimpleNamespace(attachments=[]))

    assert extract_phone_from_message(message) is None
