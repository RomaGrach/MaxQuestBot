from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from admin_panel.app import create_app
from admin_panel.config import AdminPanelSettings
from admin_panel.db import Database
from admin_panel.security import hash_password


def make_client(tmp_path: Path) -> TestClient:
    settings = AdminPanelSettings(
        db_path=str(tmp_path / "admin.sqlite3"),
        secret_key="test-secret-key",
        bootstrap_admin_username="admin",
        bootstrap_admin_password="strong-password",
    )
    return TestClient(create_app(settings))


def test_admin_dashboard_requires_login(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.get("/admin/dashboard", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"


def test_admin_login_and_dashboard(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "strong-password"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/dashboard"
    assert "set-cookie" in response.headers

    dashboard = client.get("/admin/dashboard")

    assert dashboard.status_code == 200
    assert "Dashboard" in dashboard.text
    assert "Пользователей" in dashboard.text
    assert "Авторизованные пользователи" in dashboard.text


def test_dashboard_shows_authorized_users_table(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    client.get("/admin/login")
    database = Database(str(tmp_path / "admin.sqlite3"))
    database.create_user(max_user_id="166591735", phone="+79990000000")
    database.update_user_consent("166591735")

    client.post(
        "/admin/login",
        data={"username": "admin", "password": "strong-password"},
    )

    dashboard = client.get("/admin/dashboard")

    assert dashboard.status_code == 200
    assert "166591735" in dashboard.text
    assert "+79990000000" in dashboard.text
    assert "Дата регистрации" in dashboard.text


def test_users_list_shows_completed_quests_count(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    client.get("/admin/login")
    database = Database(str(tmp_path / "admin.sqlite3"))
    user_id = database.create_user(max_user_id="777001", phone="+79991112233")
    quest_id = database.get_published_quests()[0]["id"]
    attempt_id = database.create_attempt(user_id, quest_id)
    database.complete_attempt(attempt_id)

    client.post(
        "/admin/login",
        data={"username": "admin", "password": "strong-password"},
    )
    users_page = client.get("/admin/users")

    assert users_page.status_code == 200
    assert "Квестов пройдено" in users_page.text
    assert "777001" in users_page.text
    assert ">1</td>" in users_page.text


def test_admin_can_create_quest(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    client.post(
        "/admin/login",
        data={"username": "admin", "password": "strong-password"},
    )

    response = client.post(
        "/admin/quests",
        data={
            "name": "Тестовый квест",
            "description": "Описание",
            "start_point": "Старт",
            "prize_location": "Павильон",
            "start_date": "",
            "end_date": "",
            "max_attempts": "2",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"].startswith("/admin/quests/")

    quests = client.get("/admin/quests")

    assert quests.status_code == 200
    assert "Тестовый квест" in quests.text


def test_operator_cannot_manage_quests_or_staff(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    database = Database(str(tmp_path / "admin.sqlite3"))
    database.create_admin("operator", hash_password("operator-pass"), "operator")

    client.post(
        "/admin/login",
        data={"username": "operator", "password": "operator-pass"},
    )

    users_page = client.get("/admin/users")
    assert users_page.status_code == 200

    quests_page = client.get("/admin/quests")
    assert quests_page.status_code == 200
    assert "Создать квест" not in quests_page.text

    create_form = client.get("/admin/quests/new")
    assert create_form.status_code == 403

    staff_page = client.get("/admin/staff")
    assert staff_page.status_code == 403


def test_admin_can_manage_staff_and_question_settings(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    database = Database(str(tmp_path / "admin.sqlite3"))

    client.post(
        "/admin/login",
        data={"username": "admin", "password": "strong-password"},
    )

    create_staff = client.post(
        "/admin/staff",
        data={
            "username": "quest-operator",
            "password": "secret-pass",
            "role": "operator",
        },
        follow_redirects=False,
    )
    assert create_staff.status_code == 303
    assert database.get_admin_by_username("quest-operator") is not None

    quest_id = database.get_published_quests()[0]["id"]
    create_question = client.post(
        f"/admin/quests/{quest_id}/questions",
        data={
            "order_num": "10",
            "context": "Подумайте над надписью",
            "task_text": "Какое слово видно на табличке?",
            "correct_answer": "Парк",
            "explanation": "Это ориентир у входа.",
            "hint": "Табличка на объекте у входа.",
            "semantic_mode": "contains",
            "semantic_threshold": "0.85",
            "attempts_override": "1",
        },
        follow_redirects=False,
    )
    assert create_question.status_code == 303

    question = database.get_questions_for_quest(quest_id)[-1]
    assert question["semantic_mode"] == "contains"
    assert float(question["semantic_threshold"]) == 0.85
    assert question["attempts_override"] == 1

    quest_page = client.get(f"/admin/quests/{quest_id}")
    assert quest_page.status_code == 200
    assert "contains" in quest_page.text
    assert "0.85" in quest_page.text


def test_gift_issue_form_stores_datetime_comment_and_issuer(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    database = Database(str(tmp_path / "admin.sqlite3"))
    user_id = database.create_user(max_user_id="9988", phone="+79991110000")
    quest_id = database.get_published_quests()[0]["id"]
    attempt_id = database.create_attempt(user_id, quest_id)
    database.complete_attempt(attempt_id)

    client.post(
        "/admin/login",
        data={"username": "admin", "password": "strong-password"},
    )

    response = client.post(
        f"/admin/attempts/{attempt_id}/gift",
        data={
            "gift_given_at": "2026-04-14T13:45",
            "comment": "Подарок выдан на стойке регистрации",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303

    attempt = database.get_attempt_by_id(attempt_id)
    assert attempt["gift_given"] == 1
    assert attempt["gift_given_at"].startswith("2026-04-14 13:45")
    assert attempt["comment"] == "Подарок выдан на стойке регистрации"

    attempts = database.get_attempts_for_user(user_id)
    assert attempts[0]["gift_given_by_username"] == "admin"

    detail_page = client.get(f"/admin/users/{user_id}")
    assert detail_page.status_code == 200
    assert "Подарок выдан на стойке регистрации" in detail_page.text
    assert "admin" in detail_page.text


def test_admin_export_requires_auth_and_returns_csv(tmp_path: Path) -> None:
    client = make_client(tmp_path)

    unauthorized = client.get("/admin/export", follow_redirects=False)
    assert unauthorized.status_code == 303
    assert unauthorized.headers["location"] == "/admin/login"

    client.post(
        "/admin/login",
        data={"username": "admin", "password": "strong-password"},
    )
    authorized = client.get("/admin/export")

    assert authorized.status_code == 200
    assert authorized.headers["content-type"].startswith("text/csv")
    assert "max_user_id" in authorized.text
