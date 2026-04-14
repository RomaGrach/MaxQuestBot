from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from admin_panel.app import create_app
from admin_panel.config import AdminPanelSettings


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
