from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Any

from admin_panel.db import Database, check_answer
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
    QuestStatus,
    RevealResult,
)


def _parse_datetime(raw_value: str | None) -> datetime | None:
    if not raw_value:
        return None
    value = raw_value.strip()
    if not value:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _parse_quest_boundary(raw_value: str | None, *, end_of_day: bool) -> datetime | None:
    if not raw_value:
        return None
    value = raw_value.strip()
    if not value:
        return None
    if " " in value or "T" in value:
        return _parse_datetime(value)

    parsed_date = date.fromisoformat(value)
    boundary = time.max if end_of_day else time.min
    return datetime.combine(parsed_date, boundary, UTC)


@dataclass(slots=True)
class SqliteBackendSettings:
    db_path: str = ".local/admin_panel.sqlite3"

    @property
    def resolved_db_path(self) -> Path:
        return Path(self.db_path).expanduser().resolve()


class SQLiteQuestBackend:
    def __init__(self, settings: SqliteBackendSettings | None = None) -> None:
        self.settings = settings or SqliteBackendSettings()
        self.db = Database(str(self.settings.resolved_db_path))
        self.db.init_db()

    async def ensure_user(
        self,
        max_user_id: int,
        first_name: str = "",
        last_name: str = "",
        username: str = "",
    ) -> BotUser:
        existing = self.db.get_user_by_max_id(max_user_id)
        if existing is None:
            self.db.create_user(max_user_id=max_user_id, phone=None)
            existing = self.db.get_user_by_max_id(max_user_id)
        return self._map_user(existing)

    async def get_user(self, max_user_id: int) -> BotUser | None:
        row = self.db.get_user_by_max_id(max_user_id)
        if row is None:
            return None
        return self._map_user(row)

    async def set_consent(self, max_user_id: int, consent_given: bool) -> BotUser:
        await self.ensure_user(max_user_id)
        self.db.conn.execute(
            "UPDATE users SET consent_given = ? WHERE max_user_id = ?",
            (int(consent_given), str(max_user_id)),
        )
        self.db.conn.commit()
        row = self.db.get_user_by_max_id(max_user_id)
        if row is None:
            raise ValueError(f"User {max_user_id} was not found after consent update.")
        return self._map_user(row)

    async def set_phone(self, max_user_id: int, phone: str) -> BotUser:
        await self.ensure_user(max_user_id)
        self.db.update_user_phone(max_user_id, phone.strip())
        row = self.db.get_user_by_max_id(max_user_id)
        if row is None:
            raise ValueError(f"User {max_user_id} was not found after phone update.")
        return self._map_user(row)

    async def list_available_quests(self, max_user_id: int) -> list[Quest]:
        row = self.db.get_user_by_max_id(max_user_id)
        if row is None:
            return []

        user_id = int(row["id"])
        quests: list[Quest] = []
        now = datetime.now(UTC)
        for quest_row in self.db.get_published_quests():
            if not self._is_quest_available(quest_row, now):
                continue
            quest = self._map_quest(quest_row)
            if self.db.check_gift_given(user_id, int(quest_row["id"])) is not None:
                continue
            if self.db.check_completed_quest(user_id, int(quest_row["id"])) is not None:
                continue
            quests.append(quest)
        return quests

    async def get_quest(self, quest_id: str) -> Quest | None:
        row = self.db.get_quest_by_id(int(quest_id))
        if row is None:
            return None
        return self._map_quest(row)

    async def get_active_attempt(self, max_user_id: int) -> QuestAttempt | None:
        user_row = self.db.get_user_by_max_id(max_user_id)
        if user_row is None:
            return None
        attempt_row = self.db.get_active_attempt(int(user_row["id"]))
        if attempt_row is None:
            return None
        return self._map_attempt(attempt_row)

    async def get_current_question(self, max_user_id: int) -> CurrentQuestion | None:
        user_row = self.db.get_user_by_max_id(max_user_id)
        if user_row is None:
            return None
        attempt_row = self.db.get_active_attempt(int(user_row["id"]))
        if attempt_row is None:
            return None

        quest_row = self.db.get_quest_by_id(int(attempt_row["quest_id"]))
        if quest_row is None:
            return None
        question_row = self._get_question_by_order(
            int(attempt_row["quest_id"]),
            int(attempt_row["current_question"]),
        )
        if question_row is None:
            return None

        question = self._map_question(question_row)
        attempt = self._map_attempt(attempt_row)
        progress = self._build_progress(int(attempt_row["id"]), question)
        return CurrentQuestion(
            quest=self._map_quest(quest_row),
            attempt=attempt,
            question=question,
            progress=progress,
        )

    async def start_quest(self, max_user_id: int, quest_id: str) -> QuestAttempt:
        user_row = self.db.get_user_by_max_id(max_user_id)
        if user_row is None:
            raise ValueError("Пользователь не зарегистрирован.")
        if not bool(user_row["consent_given"]):
            raise ValueError("Нужно согласиться на обработку данных перед стартом квеста.")

        quest_row = self.db.get_quest_by_id(int(quest_id))
        if quest_row is None or quest_row["status"] != QuestStatus.PUBLISHED.value:
            raise ValueError("Квест недоступен.")
        if not self._is_quest_available(quest_row, datetime.now(UTC)):
            raise ValueError("Квест сейчас недоступен по времени проведения.")

        active_attempt = self.db.get_active_attempt(int(user_row["id"]))
        if active_attempt is not None:
            if int(active_attempt["quest_id"]) == int(quest_id):
                return self._map_attempt(active_attempt)
            raise ValueError("Сначала завершите текущее прохождение.")

        if self.db.check_gift_given(int(user_row["id"]), int(quest_id)) is not None:
            raise ValueError("Приз за этот квест уже выдан, повторный запуск недоступен.")
        if self.db.check_completed_quest(int(user_row["id"]), int(quest_id)) is not None:
            raise ValueError("Квест уже завершён. Повторный запуск недоступен.")

        attempt_id = self.db.create_attempt(int(user_row["id"]), int(quest_id))
        attempt_row = self.db.get_attempt_by_id(attempt_id)
        if attempt_row is None:
            raise ValueError("Не удалось создать прохождение.")
        return self._map_attempt(attempt_row)

    async def submit_answer(self, max_user_id: int, answer: str) -> AnswerResult:
        current = await self.get_current_question(max_user_id)
        if current is None:
            raise ValueError("Сейчас нет активного вопроса.")

        attempt_id = self._find_active_attempt_id(max_user_id)
        if attempt_id is None:
            raise ValueError("Сейчас нет активного прохождения.")

        is_correct = check_answer(answer, current.question.correct_answer)
        self.db.log_answer(attempt_id, int(current.question.id), answer, is_correct)

        progress = self._build_progress(attempt_id, current.question)
        if is_correct:
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
        current = await self.get_current_question(max_user_id)
        if current is None:
            raise ValueError("Сейчас нет активного вопроса.")
        current.progress.hint_used = True
        return HintResult(
            quest=current.quest,
            question=current.question,
            hint=current.question.hint,
        )

    async def give_up(self, max_user_id: int) -> RevealResult:
        current = await self.get_current_question(max_user_id)
        if current is None:
            raise ValueError("Сейчас нет активного вопроса.")
        progress = self._build_progress(self._find_active_attempt_id(max_user_id), current.question)
        progress.resolved_by = "give_up"
        return self._advance_attempt(
            current=current,
            progress=progress,
            outcome="give_up",
        )

    def _advance_attempt(
        self,
        *,
        current: CurrentQuestion,
        progress: QuestionProgress,
        outcome: str,
    ) -> AnswerResult | RevealResult:
        attempt_id = self._find_active_attempt_id(current.attempt.user_id)
        if attempt_id is None:
            raise ValueError("Активное прохождение не найдено.")

        current_order = current.question.order
        next_question_row = self._get_question_by_order(
            int(current.quest.id),
            current_order + 1,
        )
        if next_question_row is None:
            self.db.complete_attempt(attempt_id)
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

        self.db.update_attempt_current_question(attempt_id, current_order + 1)
        next_question = self._map_question(next_question_row)
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

    def _find_active_attempt_id(self, max_user_id: int) -> int | None:
        user_row = self.db.get_user_by_max_id(max_user_id)
        if user_row is None:
            return None
        attempt_row = self.db.get_active_attempt(int(user_row["id"]))
        if attempt_row is None:
            return None
        return int(attempt_row["id"])

    def _build_progress(self, attempt_id: int | None, question: Question) -> QuestionProgress:
        attempts_used = 0
        if attempt_id is not None:
            attempts_used = self.db.conn.execute(
                "SELECT COUNT(*) FROM answer_logs WHERE attempt_id = ? AND question_id = ?",
                (attempt_id, int(question.id)),
            ).fetchone()[0]
        return QuestionProgress(
            question_id=question.id,
            attempts_used=attempts_used,
        )

    def _get_question_by_order(self, quest_id: int, order_num: int):
        return self.db.conn.execute(
            """
            SELECT * FROM questions
            WHERE quest_id = ? AND order_num = ?
            ORDER BY id
            LIMIT 1
            """,
            (quest_id, order_num),
        ).fetchone()

    def _is_quest_available(self, quest_row: Any, now: datetime) -> bool:
        start_at = _parse_quest_boundary(quest_row["start_date"], end_of_day=False)
        end_at = _parse_quest_boundary(quest_row["end_date"], end_of_day=True)
        if start_at is not None and now < start_at:
            return False
        if end_at is not None and now > end_at:
            return False
        return True

    def _resolve_attempt_limit(self, quest: Quest, question: Question) -> int:
        if question.max_attempts is not None:
            return question.max_attempts
        return quest.default_max_attempts

    def _map_user(self, row: Any) -> BotUser:
        return BotUser(
            max_user_id=int(row["max_user_id"]),
            phone=row["phone"],
            consent_given=bool(row["consent_given"]),
            created_at=_parse_datetime(row["registered_at"]) or datetime.now(UTC),
        )

    def _map_quest(self, row: Any) -> Quest:
        questions = [self._map_question(item) for item in self.db.get_questions_for_quest(int(row["id"]))]
        return Quest(
            id=str(row["id"]),
            title=row["name"],
            description=row["description"] or "",
            start_point=row["start_point"] or "",
            prize_info=row["prize_location"] or "",
            status=QuestStatus(row["status"]),
            questions=questions,
            default_max_attempts=int(row["max_attempts"] or 0),
            allow_retry_if_completed_without_prize=False,
        )

    def _map_question(self, row: Any) -> Question:
        return Question(
            id=str(row["id"]),
            order=int(row["order_num"]),
            context=row["context"] or "",
            text=row["task_text"] or "",
            correct_answer=row["correct_answer"] or "",
            answer_variants=[row["correct_answer"] or ""],
            hint=row["hint"] or "",
            explanation=row["explanation"] or "",
            max_attempts=row["attempts_override"],
        )

    def _map_attempt(self, row: Any) -> QuestAttempt:
        question_rows = self.db.get_questions_for_quest(int(row["quest_id"]))
        user_row = self.db.get_user_by_id(int(row["user_id"]))
        progress: dict[str, QuestionProgress] = {}
        for question_row in question_rows:
            question = self._map_question(question_row)
            progress[question.id] = self._build_progress(int(row["id"]), question)
        current_question_index = max(int(row["current_question"]) - 1, 0)
        return QuestAttempt(
            user_id=int(user_row["max_user_id"]) if user_row is not None else int(row["user_id"]),
            quest_id=str(row["quest_id"]),
            status=AttemptStatus(row["status"]),
            current_question_index=current_question_index,
            started_at=_parse_datetime(row["started_at"]) or datetime.now(UTC),
            completed_at=_parse_datetime(row["completed_at"]),
            prize_given=bool(row["gift_given"]),
            question_progress=progress,
        )
