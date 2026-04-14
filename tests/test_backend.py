import asyncio

from max_quest_bot.backend import InMemoryQuestBackend


def test_full_quest_happy_path() -> None:
    async def scenario() -> None:
        backend = InMemoryQuestBackend()
        await backend.ensure_user(101, first_name="Max")
        await backend.set_consent(101, True)

        quests = await backend.list_available_quests(101)
        assert len(quests) == 1

        await backend.start_quest(101, quests[0].id)
        current = await backend.get_current_question(101)
        assert current is not None
        assert current.question.id == "q1"

        result = await backend.submit_answer(101, "Огневушка")
        assert result.outcome == "correct"
        assert result.quest_completed is False

        current = await backend.get_current_question(101)
        assert current is not None
        assert current.question.id == "q2"

        await backend.submit_answer(101, "строитель")
        result = await backend.submit_answer(101, "Бажов")
        assert result.outcome == "correct"
        assert result.quest_completed is True
        assert await backend.get_current_question(101) is None

    asyncio.run(scenario())


def test_attempts_exhausted_moves_to_next_question() -> None:
    async def scenario() -> None:
        backend = InMemoryQuestBackend()
        await backend.ensure_user(202, first_name="Anna")
        await backend.set_consent(202, True)

        quests = await backend.list_available_quests(202)
        await backend.start_quest(202, quests[0].id)

        result = await backend.submit_answer(202, "неверно")
        assert result.outcome == "incorrect"
        assert result.attempts_left == 2

        await backend.submit_answer(202, "совсем неверно")
        result = await backend.submit_answer(202, "мимо")
        assert result.outcome == "attempts_exhausted"
        assert result.quest_completed is False

        current = await backend.get_current_question(202)
        assert current is not None
        assert current.question.id == "q2"

    asyncio.run(scenario())
