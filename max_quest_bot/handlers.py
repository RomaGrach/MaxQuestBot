from __future__ import annotations

from maxapi import Dispatcher, F
from maxapi.filters.contact import Contact
from maxapi.types import BotStarted, Command, Message, MessageCallback, MessageCreated

from max_quest_bot.backend import QuestBackend
from max_quest_bot.config import Settings
from max_quest_bot.keyboards import (
    active_question_keyboard,
    consent_keyboard,
    help_keyboard,
    quest_card_keyboard,
    quests_keyboard,
    request_phone_keyboard,
    start_keyboard,
)
from max_quest_bot.models import AnswerResult, CurrentQuestion, Quest, RevealResult


def extract_phone_from_message(message: Message) -> str | None:
    body = message.body
    if body is None or not body.attachments:
        return None

    for attachment in body.attachments:
        if getattr(attachment, "type", None) != "contact":
            continue
        payload = getattr(attachment, "payload", None)
        if payload is None:
            continue
        vcf = getattr(payload, "vcf", None)
        phone = getattr(vcf, "phone", None)
        if phone:
            return str(phone).strip()
    return None


def register_handlers(
    dp: Dispatcher,
    settings: Settings,
    backend: QuestBackend,
) -> None:
    async def send_message(
        message: Message,
        text: str,
        attachments: list | None = None,
    ) -> None:
        await message.answer(text=text, attachments=attachments)

    async def show_consent(message: Message) -> None:
        await send_message(
            message,
            (
                "Чтобы участвовать в квесте, нужно согласиться на обработку данных.\n\n"
                "Мы сохраняем ваш `max_user_id`, номер телефона и прогресс прохождения.\n"
                "После согласия бот попросит сразу поделиться телефоном по кнопке."
            ),
            attachments=[consent_keyboard()],
        )

    async def show_phone_request(message: Message) -> None:
        await send_message(
            message,
            (
                "Для регистрации нужно поделиться номером телефона.\n"
                "Нажмите кнопку ниже, чтобы отправить контакт и продолжить."
            ),
            attachments=[request_phone_keyboard(allow_skip=not settings.require_phone)],
        )

    async def show_registration_complete(message: Message) -> None:
        await send_message(
            message,
            (
                "Регистрация завершена.\n"
                "Это бот с городскими квестами: здесь можно выбрать квест, получить вопросы, "
                "запрашивать подсказки и пройти маршрут до конца.\n"
                "Ниже покажу доступные квесты."
            ),
            attachments=[help_keyboard()],
        )

    async def show_help(message: Message) -> None:
        await send_message(
            message,
            (
                "Команды:\n"
                "/start — начать или продолжить сценарий\n"
                "/menu — открыть меню\n"
                "/quests — показать доступные квесты\n"
                "/status — показать ваш статус\n"
                "/info — краткая информация о боте\n"
                "/help — краткая справка\n\n"
                "Во время вопроса можно отправить текстовый ответ, запросить подсказку или сдаться."
            ),
            attachments=[help_keyboard()],
        )

    async def show_info(message: Message) -> None:
        await send_message(
            message,
            (
                "Это бот городских квестов.\n"
                "Здесь можно зарегистрироваться, выбрать доступный квест, отвечать на вопросы, "
                "брать подсказки и отслеживать свой прогресс.\n\n"
                "Для быстрого доступа используйте кнопки ниже или меню команд бота."
            ),
            attachments=[help_keyboard()],
        )

    async def show_quests(message: Message, max_user_id: int) -> None:
        quests = await backend.list_available_quests(max_user_id)
        active_attempt = await backend.get_active_attempt(max_user_id)
        if active_attempt is not None:
            current = await backend.get_current_question(max_user_id)
            if current is not None:
                await send_message(
                    message,
                    (
                        "У вас уже есть активное прохождение.\n"
                        "Сначала завершите текущий квест."
                    ),
                )
                await show_current_question(message, current, intro="Продолжаем текущее прохождение.")
                return

        if not quests:
            await send_message(
                message,
                "Сейчас для вас нет доступных опубликованных квестов.",
            )
            return

        lines = ["Доступные квесты:"]
        for quest in quests:
            lines.append(f"• {quest.title}")
        await send_message(
            message,
            "\n".join(lines),
            attachments=[quests_keyboard(quests)],
        )

    async def show_status(message: Message, max_user_id: int) -> None:
        user = await backend.get_user(max_user_id)
        if user is None:
            await send_message(
                message,
                (
                    "Регистрация ещё не начата.\n"
                    "Нажмите «Старт» или используйте /start, чтобы начать."
                ),
                attachments=[start_keyboard()],
            )
            return

        parts = [
            "Ваш статус:",
            f"MAX ID: {user.max_user_id}",
            f"Согласие: {'да' if user.consent_given else 'нет'}",
            f"Телефон: {user.phone or 'не указан'}",
        ]

        active_attempt = await backend.get_active_attempt(max_user_id)
        if active_attempt is None:
            quests = await backend.list_available_quests(max_user_id)
            parts.append("Активный квест: нет")
            parts.append(f"Доступно квестов: {len(quests)}")
        else:
            quest = await backend.get_quest(active_attempt.quest_id)
            current = await backend.get_current_question(max_user_id)
            parts.append(f"Активный квест: {quest.title if quest else active_attempt.quest_id}")
            if current is None:
                parts.append("Текущий вопрос: не найден")
            else:
                parts.append(
                    f"Текущий вопрос: {current.question.order}/{len(current.quest.questions)}"
                )

        await send_message(
            message,
            "\n".join(parts),
            attachments=[help_keyboard()],
        )

    async def show_quest_card(message: Message, quest: Quest) -> None:
        text = (
            f"{quest.title}\n\n"
            f"{quest.description}\n\n"
            f"Стартовая точка: {quest.start_point}\n"
            f"Приз: {quest.prize_info}\n"
            f"Вопросов: {len(quest.questions)}"
        )
        await send_message(
            message,
            text,
            attachments=[quest_card_keyboard(quest.id)],
        )

    async def show_current_question(
        message: Message,
        current: CurrentQuestion,
        intro: str | None = None,
    ) -> None:
        question = current.question
        total = len(current.quest.questions)
        current_number = question.order
        attempts_limit = question.max_attempts
        if attempts_limit is None:
            attempts_limit = current.quest.default_max_attempts

        attempts_text = (
            "без ограничений"
            if attempts_limit == 0
            else str(max(attempts_limit - current.progress.attempts_used, 0))
        )

        parts = []
        if intro:
            parts.append(intro)
        parts.append(f"Вопрос {current_number}/{total}")
        parts.append(f"Контекст: {question.context}")
        parts.append(f"Задание: {question.text}")
        parts.append(f"Осталось попыток: {attempts_text}")
        await send_message(
            message,
            "\n\n".join(parts),
            attachments=[active_question_keyboard()],
        )

    async def show_result(
        message: Message,
        result: AnswerResult | RevealResult,
    ) -> None:
        question = result.question
        if result.outcome == "incorrect":
            attempts_left = (
                "без ограничений"
                if result.attempts_left is None
                else str(result.attempts_left)
            )
            await send_message(
                message,
                (
                    "Ответ пока не засчитан.\n"
                    f"Подсказка: {question.hint}\n"
                    f"Осталось попыток: {attempts_left}.\n"
                    "Можно попробовать ещё раз, запросить подсказку или сдаться."
                ),
                attachments=[active_question_keyboard()],
            )
            return

        if result.outcome == "correct":
            header = "Верно."
        elif result.outcome == "attempts_exhausted":
            header = "Попытки закончились."
        else:
            header = "Вопрос пропущен."

        details = (
            f"{header}\n"
            f"Правильный ответ: {question.correct_answer}\n"
            f"{question.explanation}"
        )
        await send_message(message, details)

        if result.quest_completed:
            await send_message(
                message,
                (
                    f"Квест «{result.quest.title}» завершён.\n"
                    f"Инструкция по получению приза: {result.quest.prize_info}"
                ),
            )
            return

    async def route_user(message: Message, max_user_id: int) -> None:
        user = await backend.get_user(max_user_id)
        if user is None or not user.consent_given:
            await show_consent(message)
            return
        if settings.require_phone and not user.phone:
            await show_phone_request(message)
            return
        await show_quests(message, max_user_id)

    async def resolve_current_question_after_result(
        message: Message,
        max_user_id: int,
        result: AnswerResult | RevealResult,
    ) -> None:
        await show_result(message, result)
        if result.quest_completed:
            return
        current = await backend.get_current_question(max_user_id)
        if current is not None:
            await show_current_question(message, current, intro="Следующий вопрос.")

    @dp.bot_started()
    async def on_bot_started(event: BotStarted) -> None:
        await event.bot.send_message(
            chat_id=event.chat_id,
            text=(
                "Привет! Это бот квеста.\n"
                "Нажмите кнопку «Старт», чтобы начать регистрацию и прохождение.\n"
                "Потом можно пользоваться командами /quests, /status и /info."
            ),
            attachments=[start_keyboard()],
        )

    @dp.message_created(Command(["start", "menu", "quests"]))
    async def start_command(event: MessageCreated) -> None:
        sender = event.message.sender
        await backend.ensure_user(
            max_user_id=sender.user_id,
            first_name=sender.first_name or "",
            last_name=sender.last_name or "",
            username=sender.username or "",
        )
        await route_user(event.message, sender.user_id)

    @dp.message_created(Command("help"))
    async def help_command(event: MessageCreated) -> None:
        await show_help(event.message)

    @dp.message_created(Command("info"))
    async def info_command(event: MessageCreated) -> None:
        await show_info(event.message)

    @dp.message_created(Command("status"))
    async def status_command(event: MessageCreated) -> None:
        await show_status(event.message, event.message.sender.user_id)

    @dp.message_created(Contact())
    async def contact_message(event: MessageCreated) -> None:
        sender = event.message.sender
        phone = extract_phone_from_message(event.message)
        if not phone:
            await send_message(
                event.message,
                "Не удалось извлечь телефон из контакта. Попробуйте отправить его ещё раз.",
                attachments=[request_phone_keyboard(allow_skip=not settings.require_phone)],
            )
            return

        await backend.ensure_user(
            max_user_id=sender.user_id,
            first_name=sender.first_name or "",
            last_name=sender.last_name or "",
            username=sender.username or "",
        )
        await backend.set_phone(sender.user_id, phone)
        await send_message(event.message, f"Телефон сохранён: {phone}")
        await show_registration_complete(event.message)
        await route_user(event.message, sender.user_id)

    @dp.message_created(F.message.body.text)
    async def text_message(event: MessageCreated) -> None:
        sender = event.message.sender
        text = (event.message.body.text or "").strip()
        if not text:
            return
        if text.startswith("/"):
            return

        current = await backend.get_current_question(sender.user_id)
        if current is None:
            await send_message(
                event.message,
                "Сейчас бот ждёт не текстовый ответ, а выбор действия из меню.",
                attachments=[help_keyboard()],
            )
            return

        result = await backend.submit_answer(sender.user_id, text)
        await resolve_current_question_after_result(event.message, sender.user_id, result)

    @dp.message_callback()
    async def callback_handler(event: MessageCallback) -> None:
        payload = event.callback.payload or ""
        user_id = event.callback.user.user_id
        message = event.message

        if payload == "consent:accept":
            await backend.ensure_user(
                max_user_id=user_id,
                first_name=event.callback.user.first_name or "",
                last_name=event.callback.user.last_name or "",
                username=event.callback.user.username or "",
            )
            await backend.set_consent(user_id, True)
            await event.answer(notification="Согласие сохранено.")
            if message is not None:
                await route_user(message, user_id)
            return

        if payload == "consent:decline":
            await backend.ensure_user(
                max_user_id=user_id,
                first_name=event.callback.user.first_name or "",
                last_name=event.callback.user.last_name or "",
                username=event.callback.user.username or "",
            )
            await backend.set_consent(user_id, False)
            await event.answer(notification="Без согласия участие недоступно.")
            if message is not None:
                await send_message(
                    message,
                    "Без согласия на обработку данных бот не может начать квест.",
                )
            return

        if payload == "nav:help":
            await event.answer()
            if message is not None:
                await show_help(message)
            return

        if payload == "nav:info":
            await event.answer()
            if message is not None:
                await show_info(message)
            return

        if payload == "nav:status":
            await event.answer()
            if message is not None:
                await show_status(message, user_id)
            return

        if payload == "nav:start":
            await backend.ensure_user(
                max_user_id=user_id,
                first_name=event.callback.user.first_name or "",
                last_name=event.callback.user.last_name or "",
                username=event.callback.user.username or "",
            )
            await event.answer()
            if message is not None:
                await route_user(message, user_id)
            return

        if payload == "nav:quests":
            await event.answer()
            if message is not None:
                await route_user(message, user_id)
            return

        if payload == "quest:hint":
            try:
                result = await backend.reveal_hint(user_id)
            except ValueError:
                await event.answer(notification="Сейчас нет активного вопроса.")
                return

            await event.answer(notification="Отправляю подсказку.")
            if message is not None:
                await send_message(
                    message,
                    f"Подсказка: {result.hint}",
                    attachments=[active_question_keyboard()],
                )
            return

        if payload == "quest:giveup":
            try:
                result = await backend.give_up(user_id)
            except ValueError:
                await event.answer(notification="Сейчас нет активного вопроса.")
                return

            await event.answer(notification="Показываю правильный ответ.")
            if message is not None:
                await resolve_current_question_after_result(message, user_id, result)
            return

        if payload.startswith("quest:open:"):
            quest_id = payload.removeprefix("quest:open:")
            quest = await backend.get_quest(quest_id)
            await event.answer()
            if message is not None and quest is not None:
                await show_quest_card(message, quest)
            return

        if payload.startswith("quest:start:"):
            quest_id = payload.removeprefix("quest:start:")
            try:
                await backend.start_quest(user_id, quest_id)
            except ValueError as error:
                await event.answer(notification=str(error))
                return

            await event.answer(notification="Квест запущен.")
            if message is not None:
                current = await backend.get_current_question(user_id)
                if current is not None:
                    await show_current_question(message, current, intro="Квест начат.")
            return

        await event.answer(notification="Неизвестное действие.")
