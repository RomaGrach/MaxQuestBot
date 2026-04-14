from __future__ import annotations

import re
import sqlite3
import threading
from pathlib import Path


class Database:
    def __init__(self, db_path: str) -> None:
        self.db_path = str(Path(db_path))
        self._local = threading.local()

    @property
    def conn(self) -> sqlite3.Connection:
        connection = getattr(self._local, "conn", None)
        if connection is None:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
            )
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA journal_mode = WAL")
            self._local.conn = connection
        return connection

    def close(self) -> None:
        connection = getattr(self._local, "conn", None)
        if connection is not None:
            connection.close()
            self._local.conn = None

    def init_db(
        self,
        *,
        bootstrap_admin_username: str | None = None,
        bootstrap_admin_password_hash: str | None = None,
    ) -> None:
        self._create_tables()
        self._seed_demo_data()
        if bootstrap_admin_username and bootstrap_admin_password_hash:
            self._ensure_bootstrap_admin(
                username=bootstrap_admin_username,
                password_hash=bootstrap_admin_password_hash,
            )

    def _create_tables(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'admin',
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                max_user_id TEXT UNIQUE NOT NULL,
                phone TEXT,
                registered_at TEXT DEFAULT (datetime('now')),
                consent_given INTEGER DEFAULT 0,
                comment TEXT DEFAULT '',
                bot_state TEXT DEFAULT 'new'
            );

            CREATE TABLE IF NOT EXISTS quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'draft',
                start_point TEXT DEFAULT '',
                prize_location TEXT DEFAULT '',
                start_date TEXT,
                end_date TEXT,
                max_attempts INTEGER DEFAULT 3,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quest_id INTEGER NOT NULL,
                order_num INTEGER NOT NULL,
                context TEXT DEFAULT '',
                task_text TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                explanation TEXT DEFAULT '',
                hint TEXT DEFAULT '',
                attempts_override INTEGER DEFAULT NULL,
                FOREIGN KEY (quest_id) REFERENCES quests(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS quest_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                quest_id INTEGER NOT NULL,
                status TEXT DEFAULT 'in_progress',
                current_question INTEGER DEFAULT 0,
                started_at TEXT DEFAULT (datetime('now')),
                completed_at TEXT,
                gift_given INTEGER DEFAULT 0,
                gift_given_at TEXT,
                gift_given_by INTEGER,
                comment TEXT DEFAULT '',
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (quest_id) REFERENCES quests(id),
                FOREIGN KEY (gift_given_by) REFERENCES admins(id)
            );

            CREATE TABLE IF NOT EXISTS answer_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attempt_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                answer_text TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                answered_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (attempt_id) REFERENCES quest_attempts(id),
                FOREIGN KEY (question_id) REFERENCES questions(id)
            );
            """
        )

    def _seed_demo_data(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM quests")
        if cursor.fetchone()[0] != 0:
            self.conn.commit()
            return

        cursor.execute(
            """
            INSERT INTO quests (name, description, status, start_point, prize_location, max_attempts)
            VALUES (?, ?, 'published', ?, ?, 3)
            """,
            (
                "Городской квест «Тайны парка»",
                "Увлекательный квест-прогулка по городскому парку. "
                "Найдите памятники, разгадайте загадки и узнайте интересные факты о городе.",
                "Центральный вход в городской парк",
                "Администрация парка, главное здание, 1 этаж",
            ),
        )
        quest_id = cursor.lastrowid
        questions = [
            (
                1,
                "В уральских сказах писателя Павла Бажова старатели часто рассказывают о необычной примете. "
                "Говорят, что когда рядом находится место, где можно найти золото, из огня или прямо из земли "
                "может появиться маленькая девочка. Она похожа на живую куколку и начинает быстро и ловко танцевать.",
                "Найдите памятник Огневушке-Поскакушке в сквере и прочитайте слово, которое написано на табличке под фигурой персонажа.",
                "Огневушка",
                "Огневушка-Поскакушка — персонаж уральских сказов Павла Бажова. Считается, что её появление указывает на место, где можно найти золото.",
                "Памятник находится в сквере неподалёку от главного входа. Обратите внимание на фигурку девочки.",
            ),
            (
                2,
                "В городах Урала часто устанавливали памятники людям, которые внесли значительный вклад в развитие промышленности и культуры региона.",
                "Найдите памятник основателю города рядом с аллеей и прочитайте фамилию на памятной табличке.",
                "Татищев",
                "Василий Татищев — русский историк и государственный деятель, основатель нескольких уральских городов, включая Екатеринбург.",
                "Памятник расположен на аллее рядом с фонтаном.",
            ),
            (
                3,
                "Урал славится своими полезными ископаемыми. В парке можно найти геологическую экспозицию, рассказывающую о богатствах недр.",
                "Найдите геологическую экспозицию в парке. Какой минерал, название которого переводится как «несовместимый», представлен там?",
                "Апатит",
                "Апатит — минерал, название которого происходит от греческого «апатэ» (обман). Это важнейшее сырьё для производства фосфорных удобрений.",
                "Ищите каменные образцы рядом с беседкой у пруда.",
            ),
        ]
        for question in questions:
            cursor.execute(
                """
                INSERT INTO questions (
                    quest_id,
                    order_num,
                    context,
                    task_text,
                    correct_answer,
                    explanation,
                    hint
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (quest_id, *question),
            )
        self.conn.commit()

    def _ensure_bootstrap_admin(self, *, username: str, password_hash: str) -> None:
        existing = self.get_admin_by_username(username)
        if existing is None:
            self.conn.execute(
                "INSERT INTO admins (username, password_hash, role) VALUES (?, ?, 'admin')",
                (username, password_hash),
            )
        elif existing["password_hash"] != password_hash or existing["role"] != "admin":
            self.conn.execute(
                "UPDATE admins SET password_hash = ?, role = 'admin' WHERE username = ?",
                (password_hash, username),
            )
        self.conn.commit()

    def has_admins(self) -> bool:
        return self.conn.execute("SELECT COUNT(*) FROM admins").fetchone()[0] > 0

    def get_user_by_max_id(self, max_user_id: str | int):
        return self.conn.execute(
            "SELECT * FROM users WHERE max_user_id = ?",
            (str(max_user_id),),
        ).fetchone()

    def create_user(self, max_user_id: str | int, phone: str | None = None) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO users (max_user_id, phone) VALUES (?, ?)",
            (str(max_user_id), phone),
        )
        self.conn.commit()
        return cursor.lastrowid

    def update_user_consent(self, max_user_id: str | int) -> None:
        self.conn.execute(
            "UPDATE users SET consent_given = 1, bot_state = 'selecting_quest' WHERE max_user_id = ?",
            (str(max_user_id),),
        )
        self.conn.commit()

    def update_user_state(self, max_user_id: str | int, state: str) -> None:
        self.conn.execute(
            "UPDATE users SET bot_state = ? WHERE max_user_id = ?",
            (state, str(max_user_id)),
        )
        self.conn.commit()

    def update_user_phone(self, max_user_id: str | int, phone: str) -> None:
        self.conn.execute(
            "UPDATE users SET phone = ? WHERE max_user_id = ?",
            (phone, str(max_user_id)),
        )
        self.conn.commit()

    def update_user_comment(self, user_id: int, comment: str) -> None:
        self.conn.execute(
            "UPDATE users SET comment = ? WHERE id = ?",
            (comment, user_id),
        )
        self.conn.commit()

    def get_all_users(self):
        return self.conn.execute(
            "SELECT * FROM users ORDER BY registered_at DESC"
        ).fetchall()

    def get_user_by_id(self, user_id: int):
        return self.conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

    def get_all_quests(self):
        return self.conn.execute(
            "SELECT * FROM quests ORDER BY created_at DESC"
        ).fetchall()

    def get_published_quests(self):
        return self.conn.execute(
            """
            SELECT * FROM quests
            WHERE status = 'published'
            ORDER BY created_at DESC
            """
        ).fetchall()

    def get_quest_by_id(self, quest_id: int):
        return self.conn.execute(
            "SELECT * FROM quests WHERE id = ?",
            (quest_id,),
        ).fetchone()

    def create_quest(
        self,
        name: str,
        description: str,
        start_point: str,
        prize_location: str,
        start_date: str,
        end_date: str,
        max_attempts: int,
    ) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO quests (
                name,
                description,
                start_point,
                prize_location,
                start_date,
                end_date,
                max_attempts
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                description,
                start_point,
                prize_location,
                start_date or None,
                end_date or None,
                max_attempts or 3,
            ),
        )
        self.conn.commit()
        return cursor.lastrowid

    def update_quest(
        self,
        quest_id: int,
        name: str,
        description: str,
        start_point: str,
        prize_location: str,
        start_date: str,
        end_date: str,
        max_attempts: int,
    ) -> None:
        self.conn.execute(
            """
            UPDATE quests
            SET
                name = ?,
                description = ?,
                start_point = ?,
                prize_location = ?,
                start_date = ?,
                end_date = ?,
                max_attempts = ?,
                updated_at = datetime('now')
            WHERE id = ?
            """,
            (
                name,
                description,
                start_point,
                prize_location,
                start_date or None,
                end_date or None,
                max_attempts or 3,
                quest_id,
            ),
        )
        self.conn.commit()

    def update_quest_status(self, quest_id: int, status: str) -> None:
        self.conn.execute(
            "UPDATE quests SET status = ?, updated_at = datetime('now') WHERE id = ?",
            (status, quest_id),
        )
        self.conn.commit()

    def delete_quest(self, quest_id: int) -> None:
        self.conn.execute("DELETE FROM questions WHERE quest_id = ?", (quest_id,))
        self.conn.execute("DELETE FROM quests WHERE id = ?", (quest_id,))
        self.conn.commit()

    def get_questions_for_quest(self, quest_id: int):
        return self.conn.execute(
            "SELECT * FROM questions WHERE quest_id = ? ORDER BY order_num",
            (quest_id,),
        ).fetchall()

    def get_question_by_id(self, question_id: int):
        return self.conn.execute(
            "SELECT * FROM questions WHERE id = ?",
            (question_id,),
        ).fetchone()

    def create_question(
        self,
        quest_id: int,
        order_num: int,
        context: str,
        task_text: str,
        correct_answer: str,
        explanation: str,
        hint: str,
        attempts_override: int | None = None,
    ) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO questions (
                quest_id,
                order_num,
                context,
                task_text,
                correct_answer,
                explanation,
                hint,
                attempts_override
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                quest_id,
                order_num,
                context,
                task_text,
                correct_answer,
                explanation,
                hint,
                attempts_override,
            ),
        )
        self.conn.commit()
        return cursor.lastrowid

    def update_question(
        self,
        question_id: int,
        order_num: int,
        context: str,
        task_text: str,
        correct_answer: str,
        explanation: str,
        hint: str,
        attempts_override: int | None = None,
    ) -> None:
        self.conn.execute(
            """
            UPDATE questions
            SET
                order_num = ?,
                context = ?,
                task_text = ?,
                correct_answer = ?,
                explanation = ?,
                hint = ?,
                attempts_override = ?
            WHERE id = ?
            """,
            (
                order_num,
                context,
                task_text,
                correct_answer,
                explanation,
                hint,
                attempts_override,
                question_id,
            ),
        )
        self.conn.commit()

    def delete_question(self, question_id: int) -> None:
        self.conn.execute("DELETE FROM questions WHERE id = ?", (question_id,))
        self.conn.commit()

    def get_active_attempt(self, user_id: int):
        return self.conn.execute(
            "SELECT * FROM quest_attempts WHERE user_id = ? AND status = 'in_progress'",
            (user_id,),
        ).fetchone()

    def create_attempt(self, user_id: int, quest_id: int) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO quest_attempts (user_id, quest_id, current_question) VALUES (?, ?, 1)",
            (user_id, quest_id),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_attempt_by_id(self, attempt_id: int):
        return self.conn.execute(
            "SELECT * FROM quest_attempts WHERE id = ?",
            (attempt_id,),
        ).fetchone()

    def get_attempts_for_user(self, user_id: int):
        return self.conn.execute(
            """
            SELECT qa.*, q.name AS quest_name
            FROM quest_attempts qa
            JOIN quests q ON qa.quest_id = q.id
            WHERE qa.user_id = ?
            ORDER BY qa.started_at DESC
            """,
            (user_id,),
        ).fetchall()

    def get_all_attempts(self):
        return self.conn.execute(
            """
            SELECT qa.*, q.name AS quest_name, u.max_user_id, u.phone
            FROM quest_attempts qa
            JOIN quests q ON qa.quest_id = q.id
            JOIN users u ON qa.user_id = u.id
            ORDER BY qa.started_at DESC
            """
        ).fetchall()

    def get_attempts_for_quest(self, quest_id: int):
        return self.conn.execute(
            """
            SELECT qa.*, u.max_user_id, u.phone
            FROM quest_attempts qa
            JOIN users u ON qa.user_id = u.id
            WHERE qa.quest_id = ?
            ORDER BY qa.started_at DESC
            """,
            (quest_id,),
        ).fetchall()

    def update_attempt_current_question(self, attempt_id: int, question_num: int) -> None:
        self.conn.execute(
            "UPDATE quest_attempts SET current_question = ? WHERE id = ?",
            (question_num, attempt_id),
        )
        self.conn.commit()

    def complete_attempt(self, attempt_id: int) -> None:
        self.conn.execute(
            "UPDATE quest_attempts SET status = 'completed', completed_at = datetime('now') WHERE id = ?",
            (attempt_id,),
        )
        self.conn.commit()

    def mark_gift_given(self, attempt_id: int, admin_id: int, comment: str | None = None) -> None:
        self.conn.execute(
            """
            UPDATE quest_attempts
            SET
                gift_given = 1,
                gift_given_at = datetime('now'),
                gift_given_by = ?,
                comment = ?
            WHERE id = ?
            """,
            (admin_id, comment or "", attempt_id),
        )
        self.conn.commit()

    def update_attempt_comment(self, attempt_id: int, comment: str) -> None:
        self.conn.execute(
            "UPDATE quest_attempts SET comment = ? WHERE id = ?",
            (comment, attempt_id),
        )
        self.conn.commit()

    def check_completed_quest(self, user_id: int, quest_id: int):
        return self.conn.execute(
            "SELECT * FROM quest_attempts WHERE user_id = ? AND quest_id = ? AND status = 'completed'",
            (user_id, quest_id),
        ).fetchone()

    def check_gift_given(self, user_id: int, quest_id: int):
        return self.conn.execute(
            "SELECT * FROM quest_attempts WHERE user_id = ? AND quest_id = ? AND gift_given = 1",
            (user_id, quest_id),
        ).fetchone()

    def log_answer(self, attempt_id: int, question_id: int, answer_text: str, is_correct: bool) -> None:
        self.conn.execute(
            "INSERT INTO answer_logs (attempt_id, question_id, answer_text, is_correct) VALUES (?, ?, ?, ?)",
            (attempt_id, question_id, answer_text, int(is_correct)),
        )
        self.conn.commit()

    def get_wrong_answer_count(self, attempt_id: int, question_id: int) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) FROM answer_logs WHERE attempt_id = ? AND question_id = ? AND is_correct = 0",
            (attempt_id, question_id),
        ).fetchone()
        return row[0]

    def get_answer_logs_for_attempt(self, attempt_id: int):
        return self.conn.execute(
            """
            SELECT al.*, q.task_text, q.correct_answer
            FROM answer_logs al
            JOIN questions q ON al.question_id = q.id
            WHERE al.attempt_id = ?
            ORDER BY al.answered_at
            """,
            (attempt_id,),
        ).fetchall()

    def get_admin_by_username(self, username: str):
        return self.conn.execute(
            "SELECT * FROM admins WHERE username = ?",
            (username,),
        ).fetchone()

    def get_admin_by_id(self, admin_id: int):
        return self.conn.execute(
            "SELECT * FROM admins WHERE id = ?",
            (admin_id,),
        ).fetchone()

    def get_all_admins(self):
        return self.conn.execute(
            "SELECT * FROM admins ORDER BY created_at"
        ).fetchall()

    def create_admin(self, username: str, password_hash: str, role: str = "operator") -> None:
        self.conn.execute(
            "INSERT INTO admins (username, password_hash, role) VALUES (?, ?, ?)",
            (username, password_hash, role),
        )
        self.conn.commit()

    def update_admin_password_hash(self, admin_id: int, password_hash: str) -> None:
        self.conn.execute(
            "UPDATE admins SET password_hash = ? WHERE id = ?",
            (password_hash, admin_id),
        )
        self.conn.commit()

    def get_stats(self) -> dict[str, int]:
        cursor = self.conn.cursor()
        return {
            "total_users": cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0],
            "total_quests": cursor.execute("SELECT COUNT(*) FROM quests").fetchone()[0],
            "published_quests": cursor.execute("SELECT COUNT(*) FROM quests WHERE status = 'published'").fetchone()[0],
            "completed_attempts": cursor.execute("SELECT COUNT(*) FROM quest_attempts WHERE status = 'completed'").fetchone()[0],
            "active_attempts": cursor.execute("SELECT COUNT(*) FROM quest_attempts WHERE status = 'in_progress'").fetchone()[0],
            "gifts_given": cursor.execute("SELECT COUNT(*) FROM quest_attempts WHERE gift_given = 1").fetchone()[0],
        }


def check_answer(user_answer: str, correct_answer: str) -> bool:
    user = user_answer.lower().strip()
    correct = correct_answer.lower().strip()
    if user == correct:
        return True

    user_clean = re.sub(r"[^\w\s]", "", user).strip()
    correct_clean = re.sub(r"[^\w\s]", "", correct).strip()
    if user_clean == correct_clean:
        return True
    if correct_clean in user_clean or user_clean in correct_clean:
        return True

    correct_words = set(correct_clean.split())
    user_words = set(user_clean.split())
    return bool(correct_words) and correct_words.issubset(user_words)
