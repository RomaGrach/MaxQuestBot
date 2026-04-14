from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


def utc_now() -> datetime:
    return datetime.now(UTC)


class QuestStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class AttemptStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass(slots=True)
class BotUser:
    max_user_id: int
    first_name: str = ""
    last_name: str = ""
    username: str = ""
    phone: str | None = None
    consent_given: bool = False
    created_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class Question:
    id: str
    order: int
    context: str
    text: str
    correct_answer: str
    answer_variants: list[str]
    hint: str
    explanation: str
    semantic_mode: str = "simple"
    semantic_threshold: float = 0.6
    max_attempts: int | None = None


@dataclass(slots=True)
class Quest:
    id: str
    title: str
    description: str
    start_point: str
    prize_info: str
    status: QuestStatus
    questions: list[Question]
    default_max_attempts: int = 3
    allow_retry_if_completed_without_prize: bool = False


@dataclass(slots=True)
class QuestionProgress:
    question_id: str
    attempts_used: int = 0
    hint_used: bool = False
    resolved_by: str | None = None


@dataclass(slots=True)
class QuestAttempt:
    user_id: int
    quest_id: str
    status: AttemptStatus = AttemptStatus.IN_PROGRESS
    current_question_index: int = 0
    started_at: datetime = field(default_factory=utc_now)
    completed_at: datetime | None = None
    prize_given: bool = False
    question_progress: dict[str, QuestionProgress] = field(default_factory=dict)


@dataclass(slots=True)
class CurrentQuestion:
    quest: Quest
    attempt: QuestAttempt
    question: Question
    progress: QuestionProgress


@dataclass(slots=True)
class AnswerResult:
    outcome: str
    quest: Quest
    question: Question
    progress: QuestionProgress
    attempts_left: int | None
    next_question: Question | None = None
    quest_completed: bool = False


@dataclass(slots=True)
class HintResult:
    quest: Quest
    question: Question
    hint: str


@dataclass(slots=True)
class RevealResult:
    outcome: str
    quest: Quest
    question: Question
    progress: QuestionProgress
    next_question: Question | None = None
    quest_completed: bool = False
