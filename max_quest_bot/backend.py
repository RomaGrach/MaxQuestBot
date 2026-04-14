from __future__ import annotations

import asyncio
import re
from collections import defaultdict
from datetime import datetime
from typing import Protocol

from max_quest_bot.models import (
    AnswerResult,
    AttemptStatus,
    BotUser,
    CurrentQuestion,
    HintResult,
    Quest,
    QuestAttempt,
    Question,
    QuestionProgress,
    RevealResult,
)
from max_quest_bot.sample_data import build_sample_quests
from max_quest_bot.models import QuestStatus


def normalize_answer(value: str) -> str:
    normalized = value.strip().lower().replace("ё", "е")
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


class QuestBackend(Protocol):
    async def ensure_user(
        self,
        max_user_id: int,
        first_name: str = "",
        last_name: str = "",
        username: str = "",
    ) -> BotUser: ...

    async def get_user(self, max_user_id: int) -> BotUser | None: ...

    async def set_consent(self, max_user_id: int, consent_given: bool) -> BotUser: ...

    async def set_phone(self, max_user_id: int, phone: str) -> BotUser: ...

    async def list_available_quests(self, max_user_id: int) -> list[Quest]: ...

    async def get_quest(self, quest_id: str) -> Quest | None: ...

    async def get_active_attempt(self, max_user_id: int) -> QuestAttempt | None: ...

    async def get_current_question(
        self, max_user_id: int
    ) -> CurrentQuestion | None: ...

    async def start_quest(self, max_user_id: int, quest_id: str) -> QuestAttempt: ...

    async def submit_answer(self, max_user_id: int, answer: str) -> AnswerResult: ...

    async def reveal_hint(self, max_user_id: int) -> HintResult: ...

    async def give_up(self, max_user_id: int) -> RevealResult: ...


class InMemoryQuestBackend:
    def __init__(self, quests: list[Quest] | None = None) -> None:
        self._quests = {quest.id: quest for quest in (quests or build_sample_quests())}
        self._users: dict[int, BotUser] = {}
        self._active_attempts: dict[int, QuestAttempt] = {}
        self._attempt_history: dict[int, list[QuestAttempt]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def ensure_user(
        self,
        max_user_id: int,
        first_name: str = "",
        last_name: str = "",
        username: str = "",
    ) -> BotUser:
        async with self._lock:
            user = self._users.get(max_user_id)
            if user is None:
                user = BotUser(
                    max_user_id=max_user_id,
                    first_name=first_name,
                    last_name=last_name,
                    username=username,
                )
                self._users[max_user_id] = user
                return user

            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            if username:
                user.username = username
            return user

    async def get_user(self, max_user_id: int) -> BotUser | None:
        return self._users.get(max_user_id)

    async def set_consent(self, max_user_id: int, consent_given: bool) -> BotUser:
        async with self._lock:
            user = self._require_user(max_user_id)
            user.consent_given = consent_given
            return user

    async def set_phone(self, max_user_id: int, phone: str) -> BotUser:
        async with self._lock:
            user = self._require_user(max_user_id)
            user.phone = phone
            return user

    async def list_available_quests(self, max_user_id: int) -> list[Quest]:
        available: list[Quest] = []
        user_history = self._attempt_history.get(max_user_id, [])

        for quest in self._quests.values():
            if quest.status != QuestStatus.PUBLISHED:
                continue
            if any(
                attempt.quest_id == quest.id
                and attempt.status == AttemptStatus.COMPLETED
                and (
                    attempt.prize_given
                    or not quest.allow_retry_if_completed_without_prize
                )
                for attempt in user_history
            ):
                continue
            available.append(quest)

        return sorted(available, key=lambda quest: quest.title)

    async def get_quest(self, quest_id: str) -> Quest | None:
        return self._quests.get(quest_id)

    async def get_active_attempt(self, max_user_id: int) -> QuestAttempt | None:
        return self._active_attempts.get(max_user_id)

    async def get_current_question(
        self, max_user_id: int
    ) -> CurrentQuestion | None:
        attempt = self._active_attempts.get(max_user_id)
        if attempt is None:
            return None

        quest = self._quests[attempt.quest_id]
        question = quest.questions[attempt.current_question_index]
        progress = attempt.question_progress[question.id]
        return CurrentQuestion(
            quest=quest,
            attempt=attempt,
            question=question,
            progress=progress,
        )

    async def start_quest(self, max_user_id: int, quest_id: str) -> QuestAttempt:
        async with self._lock:
            user = self._require_user(max_user_id)
            if not user.consent_given:
                raise ValueError("User must accept data processing before quest start.")

            active_attempt = self._active_attempts.get(max_user_id)
            if active_attempt is not None:
                if active_attempt.quest_id == quest_id:
                    return active_attempt
                raise ValueError("User already has another active quest.")

            quest = self._require_quest(quest_id)
            for attempt in self._attempt_history.get(max_user_id, []):
                if attempt.quest_id != quest_id:
                    continue
                if attempt.status != AttemptStatus.COMPLETED:
                    continue
                if attempt.prize_given or not quest.allow_retry_if_completed_without_prize:
                    raise ValueError("Quest is not available for repeated attempt.")

            question_progress = {
                question.id: QuestionProgress(question_id=question.id)
                for question in quest.questions
            }
            attempt = QuestAttempt(
                user_id=max_user_id,
                quest_id=quest_id,
                question_progress=question_progress,
            )
            self._active_attempts[max_user_id] = attempt
            self._attempt_history[max_user_id].append(attempt)
            return attempt

    async def submit_answer(self, max_user_id: int, answer: str) -> AnswerResult:
        async with self._lock:
            current = self._require_current_question(max_user_id)
            progress = current.progress
            progress.attempts_used += 1

            if self._is_correct_answer(current.question, answer):
                progress.resolved_by = "correct"
                return self._advance_attempt(
                    current=current,
                    progress=progress,
                    outcome="correct",
                )

            attempts_limit = self._resolve_attempt_limit(current.quest, current.question)
            if attempts_limit == 0:
                return AnswerResult(
                    outcome="incorrect",
                    quest=current.quest,
                    question=current.question,
                    progress=progress,
                    attempts_left=None,
                )

            attempts_left = max(attempts_limit - progress.attempts_used, 0)
            if attempts_left > 0:
                return AnswerResult(
                    outcome="incorrect",
                    quest=current.quest,
                    question=current.question,
                    progress=progress,
                    attempts_left=attempts_left,
                )

            progress.resolved_by = "attempts_exhausted"
            return self._advance_attempt(
                current=current,
                progress=progress,
                outcome="attempts_exhausted",
            )

    async def reveal_hint(self, max_user_id: int) -> HintResult:
        async with self._lock:
            current = self._require_current_question(max_user_id)
            current.progress.hint_used = True
            return HintResult(
                quest=current.quest,
                question=current.question,
                hint=current.question.hint,
            )

    async def give_up(self, max_user_id: int) -> RevealResult:
        async with self._lock:
            current = self._require_current_question(max_user_id)
            current.progress.resolved_by = "give_up"
            return self._advance_attempt(
                current=current,
                progress=current.progress,
                outcome="give_up",
            )

    def _advance_attempt(
        self,
        current: CurrentQuestion,
        progress: QuestionProgress,
        outcome: str,
    ) -> AnswerResult | RevealResult:
        attempt = current.attempt
        attempt.current_question_index += 1
        if attempt.current_question_index >= len(current.quest.questions):
            attempt.status = AttemptStatus.COMPLETED
            attempt.completed_at = datetime.utcnow()
            self._active_attempts.pop(attempt.user_id, None)
            if outcome in {"correct", "attempts_exhausted"}:
                return AnswerResult(
                    outcome=outcome,
                    quest=current.quest,
                    question=current.question,
                    progress=progress,
                    attempts_left=0,
                    quest_completed=True,
                )
            return RevealResult(
                outcome=outcome,
                quest=current.quest,
                question=current.question,
                progress=progress,
                quest_completed=True,
            )

        next_question = current.quest.questions[attempt.current_question_index]
        if outcome in {"correct", "attempts_exhausted"}:
            return AnswerResult(
                outcome=outcome,
                quest=current.quest,
                question=current.question,
                progress=progress,
                attempts_left=0 if outcome == "attempts_exhausted" else None,
                next_question=next_question,
            )
        return RevealResult(
            outcome=outcome,
            quest=current.quest,
            question=current.question,
            progress=progress,
            next_question=next_question,
        )

    def _require_user(self, max_user_id: int) -> BotUser:
        user = self._users.get(max_user_id)
        if user is None:
            raise ValueError(f"User {max_user_id} is not registered.")
        return user

    def _require_quest(self, quest_id: str) -> Quest:
        quest = self._quests.get(quest_id)
        if quest is None:
            raise ValueError(f"Quest '{quest_id}' does not exist.")
        return quest

    def _require_current_question(self, max_user_id: int) -> CurrentQuestion:
        attempt = self._active_attempts.get(max_user_id)
        if attempt is None:
            raise ValueError("There is no active quest attempt for this user.")

        quest = self._quests[attempt.quest_id]
        question = quest.questions[attempt.current_question_index]
        progress = attempt.question_progress[question.id]
        return CurrentQuestion(
            quest=quest,
            attempt=attempt,
            question=question,
            progress=progress,
        )

    @staticmethod
    def _resolve_attempt_limit(quest: Quest, question: Question) -> int:
        if question.max_attempts is not None:
            return question.max_attempts
        return quest.default_max_attempts

    @staticmethod
    def _is_correct_answer(question: Question, answer: str) -> bool:
        user_answer = normalize_answer(answer)
        return any(
            normalize_answer(variant) == user_answer
            for variant in question.answer_variants
        )
