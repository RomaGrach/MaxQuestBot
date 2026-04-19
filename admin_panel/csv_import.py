from __future__ import annotations

import csv
import io
from dataclasses import dataclass


EXPECTED_CSV_HEADERS = [
    "question_order",
    "context",
    "question_text",
    "correct_answer",
    "hint",
    "answer_explanation",
]


@dataclass(slots=True)
class ImportedQuestion:
    order_num: int
    context: str
    task_text: str
    correct_answer: str
    hint: str
    explanation: str


@dataclass(slots=True)
class QuestCSVImport:
    quest_name: str
    questions: list[ImportedQuestion]


def parse_quest_csv_import(
    *,
    quest_name: str,
    filename: str | None,
    content: bytes | None,
) -> tuple[QuestCSVImport | None, list[str]]:
    errors: list[str] = []
    normalized_name = quest_name.strip()
    if not normalized_name:
        errors.append("Не указано название квеста")

    normalized_filename = (filename or "").strip()
    if not normalized_filename:
        errors.append("Не выбран CSV-файл")
    elif not normalized_filename.lower().endswith(".csv"):
        errors.append("Неверный формат файла. Требуется CSV")

    if content is None:
        return None, errors

    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        errors.append("Файл должен быть в кодировке UTF-8")
        return None, errors

    try:
        rows = list(csv.reader(io.StringIO(decoded, newline="")))
    except csv.Error:
        errors.append("Некорректная строка заголовков CSV")
        return None, errors

    if not rows:
        errors.append("Некорректная строка заголовков CSV")
        return None, errors

    header = rows[0]
    if header != EXPECTED_CSV_HEADERS:
        missing_columns = [column for column in EXPECTED_CSV_HEADERS if column not in header]
        for column in missing_columns:
            errors.append(f"Отсутствует обязательный столбец {column}")

        if (
            len(header) == len(EXPECTED_CSV_HEADERS)
            and set(header) == set(EXPECTED_CSV_HEADERS)
            and not missing_columns
        ):
            errors.append("Неверный порядок столбцов в CSV-файле")
        else:
            errors.append("Некорректная строка заголовков CSV")
        return None, errors

    data_rows = rows[1:]
    if not data_rows:
        errors.append("Файл не содержит ни одного вопроса")
        return None, errors

    seen_orders: set[int] = set()
    questions: list[ImportedQuestion] = []
    required_fields = set(EXPECTED_CSV_HEADERS)

    for line_number, row in enumerate(data_rows, start=2):
        if not row or all(not cell.strip() for cell in row):
            errors.append(f"Строка {line_number}: пустая строка не допускается")
            continue

        if len(row) != len(EXPECTED_CSV_HEADERS):
            errors.append(f"Строка {line_number}: неверное количество столбцов")
            continue

        row_data = dict(zip(EXPECTED_CSV_HEADERS, row, strict=True))
        normalized_row = {key: value.strip() for key, value in row_data.items()}

        for field_name in EXPECTED_CSV_HEADERS:
            if field_name in required_fields and not normalized_row[field_name]:
                errors.append(f"Строка {line_number}: не заполнено поле {field_name}")

        raw_order = normalized_row["question_order"]
        try:
            order_num = int(raw_order)
            if order_num <= 0:
                raise ValueError
        except ValueError:
            errors.append(
                f"Строка {line_number}: значение question_order должно быть положительным целым числом"
            )
            continue

        if order_num in seen_orders:
            errors.append(f"Строка {line_number}: question_order повторяется")
            continue
        seen_orders.add(order_num)

        if any(
            not normalized_row[field_name]
            for field_name in (
                "context",
                "question_text",
                "correct_answer",
                "hint",
                "answer_explanation",
            )
        ):
            continue

        questions.append(
            ImportedQuestion(
                order_num=order_num,
                context=normalized_row["context"],
                task_text=normalized_row["question_text"],
                correct_answer=normalized_row["correct_answer"],
                hint=normalized_row["hint"],
                explanation=normalized_row["answer_explanation"],
            )
        )

    if errors:
        return None, errors

    questions.sort(key=lambda question: question.order_num)
    return QuestCSVImport(quest_name=normalized_name, questions=questions), []
