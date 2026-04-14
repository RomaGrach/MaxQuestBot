from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from admin_panel.app import create_app
from admin_panel.config import AdminPanelSettings
from admin_panel.db import Database


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
