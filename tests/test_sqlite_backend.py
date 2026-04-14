from __future__ import annotations

import asyncio
import re
from pathlib import Path

from fastapi.testclient import TestClient

from admin_panel.app import create_app
from admin_panel.config import AdminPanelSettings
from max_quest_bot.sqlite_backend import SQLiteQuestBackend, SqliteBackendSettings


def make_backend(tmp_path: Path) -> SQLiteQuestBackend:
    return SQLiteQuestBackend(
        SqliteBackendSettings(db_path=str(tmp_path / "shared.sqlite3"))
    )


def make_admin_client(tmp_path: Path) -> TestClient:
    settings = AdminPanelSettings(
        db_path=str(tmp_path / "shared.sqlite3"),
        secret_key="test-secret-key",
        bootstrap_admin_username="admin",
        bootstrap_admin_password="strong-password",
    )
    return TestClient(create_app(settings))


def test_sqlite_backend_persists_bot_state_for_admin_panel(tmp_path: Path) -> None:
    async def scenario() -> None:
        backend = make_backend(tmp_path)
        await backend.ensure_user(404)
        await backend.set_consent(404, True)

        quests = await backend.list_available_quests(404)
        assert len(quests) == 1

        await backend.start_quest(404, quests[0].id)
        result = await backend.submit_answer(404, "неверно")
        assert result.outcome == "incorrect"

    asyncio.run(scenario())

    client = make_admin_client(tmp_path)
    login = client.post(
        "/admin/login",
        data={"username": "admin", "password": "strong-password"},
        follow_redirects=False,
    )
    assert login.status_code == 303

    dashboard = client.get("/admin/dashboard")
    assert dashboard.status_code == 200
    assert re.search(r'<div class="num">1</div><div class="label">Пользователей</div>', dashboard.text)
    assert re.search(r'<div class="num">1</div><div class="label">Активных прохождений</div>', dashboard.text)

    users = client.get("/admin/users")
    assert users.status_code == 200
    assert "404" in users.text


def test_sqlite_backend_completes_quest_and_updates_stats(tmp_path: Path) -> None:
    async def scenario() -> None:
        backend = make_backend(tmp_path)
        await backend.ensure_user(505)
        await backend.set_consent(505, True)

        quests = await backend.list_available_quests(505)
        await backend.start_quest(505, quests[0].id)
        await backend.submit_answer(505, "Огневушка")
        await backend.submit_answer(505, "Татищев")
        result = await backend.submit_answer(505, "Апатит")

        assert result.outcome == "correct"
        assert result.quest_completed is True

    asyncio.run(scenario())

    client = make_admin_client(tmp_path)
    client.post(
        "/admin/login",
        data={"username": "admin", "password": "strong-password"},
    )
    stats = client.get("/admin/stats")

    assert stats.status_code == 200
    assert re.search(r'<div class="num">1</div><div class="label">Пользователей</div>', stats.text)
    assert re.search(r'<div class="num">1</div><div class="label">Завершённых прохождений</div>', stats.text)
    assert re.search(r'<div class="num">0</div><div class="label">Активных прохождений</div>', stats.text)
