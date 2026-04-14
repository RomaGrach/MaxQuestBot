from __future__ import annotations

import csv
import io
import sqlite3
from contextlib import asynccontextmanager, suppress
from typing import Any

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, Response

from admin_panel.config import AdminPanelSettings
from admin_panel.db import Database
from admin_panel.security import (
    hash_password,
    make_session_token,
    parse_session_token,
    verify_password,
)
from admin_panel import views


def create_app(settings: AdminPanelSettings | None = None) -> FastAPI:
    resolved_settings = settings or AdminPanelSettings.from_env()
    resolved_settings.validate()
    database = Database(str(resolved_settings.resolved_db_path))
    bootstrap_password_hash = (
        hash_password(resolved_settings.bootstrap_admin_password)
        if resolved_settings.bootstrap_admin_username
        and resolved_settings.bootstrap_admin_password
        else None
    )
    database.init_db(
        bootstrap_admin_username=resolved_settings.bootstrap_admin_username,
        bootstrap_admin_password_hash=bootstrap_password_hash,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        yield
        with suppress(Exception):
            database.close()

    app = FastAPI(title="MaxQuestBot Admin Panel", lifespan=lifespan)
    app.state.settings = resolved_settings
    app.state.db = database

    def get_db() -> Database:
        return app.state.db

    def get_settings() -> AdminPanelSettings:
        return app.state.settings

    def get_current_admin(request: Request):
        token = request.cookies.get(get_settings().session_cookie_name)
        if not token:
            return None
        username = parse_session_token(token, get_settings().secret_key)
        if not username:
            return None
        return get_db().get_admin_by_username(username)

    def render_html(
        content: str,
        *,
        user=None,
        status_code: int = 200,
    ) -> HTMLResponse:
        response = HTMLResponse(content=content, status_code=status_code)
        if user is not None:
            _set_session_cookie(response, username=user["username"])
        return response

    def _set_session_cookie(response: Response, *, username: str) -> None:
        settings = get_settings()
        response.set_cookie(
            key=settings.session_cookie_name,
            value=make_session_token(
                username=username,
                secret_key=settings.secret_key,
                max_age=settings.session_max_age,
            ),
            max_age=settings.session_max_age,
            httponly=True,
            samesite="strict",
            secure=settings.session_cookie_secure,
            path="/",
        )

    def login_redirect() -> RedirectResponse:
        return RedirectResponse(url="/admin/login", status_code=303)

    def require_admin(request: Request):
        admin = get_current_admin(request)
        if admin is None:
            return None, login_redirect()
        return admin, None

    def require_role(request: Request, *roles: str):
        admin, redirect = require_admin(request)
        if redirect:
            return None, redirect
        if roles and admin["role"] not in roles:
            return admin, PlainTextResponse("Forbidden", status_code=403)
        return admin, None

    def require_superadmin(request: Request):
        return require_role(request, "admin")

    def _is_truthy(raw_value: str | None) -> bool:
        if raw_value is None:
            return False
        return raw_value.strip().lower() in {"1", "true", "yes", "y", "on"}

    def _normalize_gift_datetime(raw_value: str) -> str | None:
        value = raw_value.strip()
        if not value:
            return None
        value = value.replace("T", " ")
        if len(value) == 16:
            return f"{value}:00"
        return value

    def _render_staff_page(
        *,
        current_admin,
        error: str = "",
    ) -> HTMLResponse:
        return render_html(
            views.staff_page(get_db().get_all_admins(), current_admin, error=error),
            user=current_admin,
        )

    def _quest_id_from_question(question) -> int:
        return int(question["quest_id"])

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request):
        admin = get_current_admin(request)
        if admin is None:
            return login_redirect()
        return RedirectResponse(url="/admin/dashboard", status_code=303)

    @app.get("/admin/login", response_class=HTMLResponse)
    async def admin_login_page(request: Request):
        if get_current_admin(request) is not None:
            return RedirectResponse(url="/admin/dashboard", status_code=303)
        error = ""
        if not get_db().has_admins():
            error = (
                "Администратор не создан. Укажите "
                "ADMIN_PANEL_BOOTSTRAP_USERNAME и ADMIN_PANEL_BOOTSTRAP_PASSWORD."
            )
        return render_html(views.login_page(error))

    @app.post("/admin/login")
    async def admin_login_submit(
        username: str = Form(default=""),
        password: str = Form(default=""),
    ):
        admin = get_db().get_admin_by_username(username)
        if admin is None or not verify_password(password, admin["password_hash"]):
            return render_html(
                views.login_page("Неверный логин или пароль"),
                status_code=401,
            )
        if not str(admin["password_hash"]).startswith("scrypt$"):
            get_db().update_admin_password_hash(admin["id"], hash_password(password))
        response = RedirectResponse(url="/admin/dashboard", status_code=303)
        _set_session_cookie(response, username=admin["username"])
        return response

    @app.get("/admin/logout")
    async def admin_logout():
        response = RedirectResponse(url="/admin/login", status_code=303)
        response.delete_cookie(key=get_settings().session_cookie_name, path="/")
        return response

    @app.get("/admin/dashboard", response_class=HTMLResponse)
    async def admin_dashboard(request: Request):
        admin, redirect = require_admin(request)
        if redirect:
            return redirect
        return render_html(
            views.dashboard(get_db().get_stats(), get_db().get_all_users(), user=admin),
            user=admin,
        )

    @app.get("/admin/users", response_class=HTMLResponse)
    async def admin_users(request: Request):
        admin, redirect = require_admin(request)
        if redirect:
            return redirect
        return render_html(
            views.users_list(get_db().get_all_users(), user=admin),
            user=admin,
        )

    @app.get("/admin/users/{user_id}", response_class=HTMLResponse)
    async def admin_user_detail(user_id: int, request: Request):
        admin, redirect = require_admin(request)
        if redirect:
            return redirect
        user = get_db().get_user_by_id(user_id)
        if user is None:
            return PlainTextResponse("User not found", status_code=404)
        attempts = get_db().get_attempts_for_user(user_id)
        logs_map = {
            attempt["id"]: get_db().get_answer_logs_for_attempt(attempt["id"])
            for attempt in attempts
        }
        return render_html(
            views.user_detail(user, attempts, logs_map, admin),
            user=admin,
        )

    @app.post("/admin/users/{user_id}/comment")
    async def admin_user_comment(
        user_id: int,
        request: Request,
        comment: str = Form(default=""),
    ):
        admin, redirect = require_admin(request)
        if redirect:
            return redirect
        if get_db().get_user_by_id(user_id) is None:
            return PlainTextResponse("User not found", status_code=404)
        get_db().update_user_comment(user_id, comment)
        response = RedirectResponse(url=f"/admin/users/{user_id}", status_code=303)
        _set_session_cookie(response, username=admin["username"])
        return response

    @app.get("/admin/quests", response_class=HTMLResponse)
    async def admin_quests(request: Request):
        admin, redirect = require_admin(request)
        if redirect:
            return redirect
        return render_html(
            views.quests_list(get_db().get_all_quests(), user=admin),
            user=admin,
        )

    @app.get("/admin/quests/new", response_class=HTMLResponse)
    async def admin_quest_form(request: Request):
        admin, redirect = require_superadmin(request)
        if redirect:
            return redirect
        return render_html(views.quest_form(user=admin), user=admin)

    @app.post("/admin/quests")
    async def admin_quest_create(
        request: Request,
        name: str = Form(...),
        description: str = Form(default=""),
        start_point: str = Form(default=""),
        prize_location: str = Form(default=""),
        start_date: str = Form(default=""),
        end_date: str = Form(default=""),
        max_attempts: int = Form(default=3),
        allow_retry_before_gift: str = Form(default=""),
    ):
        admin, redirect = require_superadmin(request)
        if redirect:
            return redirect
        quest_id = get_db().create_quest(
            name,
            description,
            start_point,
            prize_location,
            start_date,
            end_date,
            max_attempts,
            _is_truthy(allow_retry_before_gift),
        )
        response = RedirectResponse(url=f"/admin/quests/{quest_id}", status_code=303)
        _set_session_cookie(response, username=admin["username"])
        return response

    @app.get("/admin/quests/{quest_id}", response_class=HTMLResponse)
    async def admin_quest_detail(quest_id: int, request: Request):
        admin, redirect = require_admin(request)
        if redirect:
            return redirect
        quest = get_db().get_quest_by_id(quest_id)
        if quest is None:
            return PlainTextResponse("Quest not found", status_code=404)
        questions = get_db().get_questions_for_quest(quest_id)
        attempts = get_db().get_attempts_for_quest(quest_id)
        return render_html(
            views.quest_detail(quest, questions, attempts, user=admin),
            user=admin,
        )

    @app.get("/admin/quests/{quest_id}/edit", response_class=HTMLResponse)
    async def admin_quest_edit_form(quest_id: int, request: Request):
        admin, redirect = require_superadmin(request)
        if redirect:
            return redirect
        quest = get_db().get_quest_by_id(quest_id)
        if quest is None:
            return PlainTextResponse("Quest not found", status_code=404)
        return render_html(views.quest_form(dict(quest), user=admin), user=admin)

    @app.post("/admin/quests/{quest_id}")
    async def admin_quest_update(
        quest_id: int,
        request: Request,
        name: str = Form(...),
        description: str = Form(default=""),
        start_point: str = Form(default=""),
        prize_location: str = Form(default=""),
        start_date: str = Form(default=""),
        end_date: str = Form(default=""),
        max_attempts: int = Form(default=3),
        allow_retry_before_gift: str = Form(default=""),
    ):
        admin, redirect = require_superadmin(request)
        if redirect:
            return redirect
        if get_db().get_quest_by_id(quest_id) is None:
            return PlainTextResponse("Quest not found", status_code=404)
        get_db().update_quest(
            quest_id,
            name,
            description,
            start_point,
            prize_location,
            start_date,
            end_date,
            max_attempts,
            _is_truthy(allow_retry_before_gift),
        )
        response = RedirectResponse(url=f"/admin/quests/{quest_id}", status_code=303)
        _set_session_cookie(response, username=admin["username"])
        return response

    @app.post("/admin/quests/{quest_id}/publish")
    async def admin_quest_publish(quest_id: int, request: Request):
        admin, redirect = require_superadmin(request)
        if redirect:
            return redirect
        get_db().update_quest_status(quest_id, "published")
        response = RedirectResponse(url=f"/admin/quests/{quest_id}", status_code=303)
        _set_session_cookie(response, username=admin["username"])
        return response

    @app.post("/admin/quests/{quest_id}/archive")
    async def admin_quest_archive(quest_id: int, request: Request):
        admin, redirect = require_superadmin(request)
        if redirect:
            return redirect
        get_db().update_quest_status(quest_id, "archived")
        response = RedirectResponse(url=f"/admin/quests/{quest_id}", status_code=303)
        _set_session_cookie(response, username=admin["username"])
        return response

    @app.post("/admin/quests/{quest_id}/delete")
    async def admin_quest_delete(quest_id: int, request: Request):
        admin, redirect = require_superadmin(request)
        if redirect:
            return redirect
        get_db().delete_quest(quest_id)
        response = RedirectResponse(url="/admin/quests", status_code=303)
        _set_session_cookie(response, username=admin["username"])
        return response

    @app.get("/admin/quests/{quest_id}/questions/new", response_class=HTMLResponse)
    async def admin_question_new_form(quest_id: int, request: Request):
        admin, redirect = require_superadmin(request)
        if redirect:
            return redirect
        if get_db().get_quest_by_id(quest_id) is None:
            return PlainTextResponse("Quest not found", status_code=404)
        return render_html(views.question_form(quest_id, user=admin), user=admin)

    @app.post("/admin/quests/{quest_id}/questions")
    async def admin_question_create(
        quest_id: int,
        request: Request,
        order_num: int = Form(default=1),
        context: str = Form(default=""),
        task_text: str = Form(...),
        correct_answer: str = Form(...),
        explanation: str = Form(default=""),
        hint: str = Form(default=""),
        semantic_mode: str = Form(default="simple"),
        semantic_threshold: float = Form(default=0.6),
        attempts_override: str = Form(default=""),
    ):
        admin, redirect = require_superadmin(request)
        if redirect:
            return redirect
        if get_db().get_quest_by_id(quest_id) is None:
            return PlainTextResponse("Quest not found", status_code=404)
        get_db().create_question(
            quest_id,
            order_num,
            context,
            task_text,
            correct_answer,
            explanation,
            hint,
            semantic_mode.strip().lower() or "simple",
            semantic_threshold,
            int(attempts_override) if attempts_override.strip() else None,
        )
        response = RedirectResponse(url=f"/admin/quests/{quest_id}", status_code=303)
        _set_session_cookie(response, username=admin["username"])
        return response

    @app.post("/admin/quests/{quest_id}/questions/import")
    async def admin_questions_import(
        quest_id: int,
        request: Request,
        csv_file: UploadFile = File(...),
    ):
        admin, redirect = require_superadmin(request)
        if redirect:
            return redirect
        if get_db().get_quest_by_id(quest_id) is None:
            return PlainTextResponse("Quest not found", status_code=404)
        content = (await csv_file.read()).decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))
        existing = get_db().get_questions_for_quest(quest_id)
        next_order = max((question["order_num"] for question in existing), default=0) + 1
        for row in reader:
            get_db().create_question(
                quest_id=quest_id,
                order_num=int(row.get("order_num", next_order)),
                context=row.get("context", ""),
                task_text=row.get("task_text", ""),
                correct_answer=row.get("correct_answer", ""),
                explanation=row.get("explanation", ""),
                hint=row.get("hint", ""),
                semantic_mode=(row.get("semantic_mode", "simple") or "simple").strip().lower(),
                semantic_threshold=float(row.get("semantic_threshold", 0.6) or 0.6),
                attempts_override=(
                    int(row["attempts_override"])
                    if row.get("attempts_override", "").strip()
                    else None
                ),
            )
            next_order += 1
        response = RedirectResponse(url=f"/admin/quests/{quest_id}", status_code=303)
        _set_session_cookie(response, username=admin["username"])
        return response

    @app.get("/admin/questions/{question_id}/edit", response_class=HTMLResponse)
    async def admin_question_edit_form(question_id: int, request: Request):
        admin, redirect = require_superadmin(request)
        if redirect:
            return redirect
        question = get_db().get_question_by_id(question_id)
        if question is None:
            return PlainTextResponse("Question not found", status_code=404)
        return render_html(
            views.question_form(
                _quest_id_from_question(question),
                dict(question),
                user=admin,
            ),
            user=admin,
        )

    @app.post("/admin/questions/{question_id}")
    async def admin_question_update(
        question_id: int,
        request: Request,
        order_num: int = Form(default=1),
        context: str = Form(default=""),
        task_text: str = Form(...),
        correct_answer: str = Form(...),
        explanation: str = Form(default=""),
        hint: str = Form(default=""),
        semantic_mode: str = Form(default="simple"),
        semantic_threshold: float = Form(default=0.6),
        attempts_override: str = Form(default=""),
    ):
        admin, redirect = require_superadmin(request)
        if redirect:
            return redirect
        question = get_db().get_question_by_id(question_id)
        if question is None:
            return PlainTextResponse("Question not found", status_code=404)
        get_db().update_question(
            question_id=question_id,
            order_num=order_num,
            context=context,
            task_text=task_text,
            correct_answer=correct_answer,
            explanation=explanation,
            hint=hint,
            semantic_mode=semantic_mode.strip().lower() or "simple",
            semantic_threshold=semantic_threshold,
            attempts_override=int(attempts_override) if attempts_override.strip() else None,
        )
        response = RedirectResponse(
            url=f"/admin/quests/{question['quest_id']}",
            status_code=303,
        )
        _set_session_cookie(response, username=admin["username"])
        return response

    @app.post("/admin/questions/{question_id}/delete")
    async def admin_question_delete(question_id: int, request: Request):
        admin, redirect = require_superadmin(request)
        if redirect:
            return redirect
        question = get_db().get_question_by_id(question_id)
        if question is None:
            return PlainTextResponse("Question not found", status_code=404)
        quest_id = question["quest_id"]
        get_db().delete_question(question_id)
        response = RedirectResponse(url=f"/admin/quests/{quest_id}", status_code=303)
        _set_session_cookie(response, username=admin["username"])
        return response

    @app.post("/admin/attempts/{attempt_id}/gift")
    async def admin_attempt_gift(
        attempt_id: int,
        request: Request,
        gift_given_at: str = Form(default=""),
        comment: str = Form(default=""),
    ):
        admin, redirect = require_admin(request)
        if redirect:
            return redirect
        attempt = get_db().get_attempt_by_id(attempt_id)
        if attempt is None or attempt["status"] != "completed":
            return PlainTextResponse("Attempt not found", status_code=404)
        get_db().mark_gift_given(
            attempt_id,
            admin["id"],
            gift_given_at=_normalize_gift_datetime(gift_given_at),
            comment=comment.strip() or None,
        )
        response = RedirectResponse(url=f"/admin/users/{attempt['user_id']}", status_code=303)
        _set_session_cookie(response, username=admin["username"])
        return response

    @app.post("/admin/attempts/{attempt_id}/comment")
    async def admin_attempt_comment(
        attempt_id: int,
        request: Request,
        comment: str = Form(default=""),
    ):
        admin, redirect = require_admin(request)
        if redirect:
            return redirect
        attempt = get_db().get_attempt_by_id(attempt_id)
        if attempt is None:
            return PlainTextResponse("Attempt not found", status_code=404)
        get_db().update_attempt_comment(attempt_id, comment)
        response = RedirectResponse(url=f"/admin/users/{attempt['user_id']}", status_code=303)
        _set_session_cookie(response, username=admin["username"])
        return response

    @app.get("/admin/stats", response_class=HTMLResponse)
    async def admin_stats(request: Request):
        admin, redirect = require_admin(request)
        if redirect:
            return redirect
        return render_html(views.stats_page(get_db().get_stats(), user=admin), user=admin)

    @app.get("/admin/export")
    async def admin_export(request: Request):
        admin, redirect = require_admin(request)
        if redirect:
            return redirect
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "max_user_id",
                "телефон",
                "квест",
                "статус",
                "дата_начала",
                "дата_завершения",
                "подарок_выдан",
                "дата_выдачи_подарка",
                "кто_выдал_подарок",
                "комментарий",
            ]
        )
        for attempt in get_db().get_all_attempts():
            writer.writerow(
                [
                    attempt["max_user_id"],
                    attempt["phone"] or "",
                    attempt["quest_name"],
                    attempt["status"],
                    attempt["started_at"] or "",
                    attempt["completed_at"] or "",
                    "да" if attempt["gift_given"] else "нет",
                    attempt["gift_given_at"] or "",
                    attempt["gift_given_by_username"] or "",
                    attempt["comment"] or "",
                ]
            )
        response = Response(
            content=output.getvalue().encode("utf-8-sig"),
            media_type="text/csv; charset=utf-8",
        )
        response.headers["Content-Disposition"] = "attachment; filename=quest_stats.csv"
        _set_session_cookie(response, username=admin["username"])
        return response

    @app.get("/admin/staff", response_class=HTMLResponse)
    async def admin_staff(request: Request):
        admin, redirect = require_superadmin(request)
        if redirect:
            return redirect
        return _render_staff_page(current_admin=admin)

    @app.post("/admin/staff")
    async def admin_staff_create(
        request: Request,
        username: str = Form(default=""),
        password: str = Form(default=""),
        role: str = Form(default="operator"),
    ):
        admin, redirect = require_superadmin(request)
        if redirect:
            return redirect

        normalized_username = username.strip()
        normalized_role = role.strip().lower() or "operator"
        if not normalized_username or not password.strip():
            return _render_staff_page(
                current_admin=admin,
                error="Укажите логин и пароль для нового сотрудника.",
            )
        if normalized_role not in {"admin", "operator"}:
            return _render_staff_page(
                current_admin=admin,
                error="Недопустимая роль сотрудника.",
            )

        try:
            get_db().create_admin(
                normalized_username,
                hash_password(password.strip()),
                normalized_role,
            )
        except sqlite3.IntegrityError:
            return _render_staff_page(
                current_admin=admin,
                error="Сотрудник с таким логином уже существует.",
            )

        response = RedirectResponse(url="/admin/staff", status_code=303)
        _set_session_cookie(response, username=admin["username"])
        return response

    @app.post("/admin/staff/{admin_id}")
    async def admin_staff_update(
        admin_id: int,
        request: Request,
        role: str = Form(default="operator"),
        password: str = Form(default=""),
    ):
        admin, redirect = require_superadmin(request)
        if redirect:
            return redirect

        target_admin = get_db().get_admin_by_id(admin_id)
        if target_admin is None:
            return PlainTextResponse("Admin not found", status_code=404)

        normalized_role = role.strip().lower() or "operator"
        if normalized_role not in {"admin", "operator"}:
            return _render_staff_page(
                current_admin=admin,
                error="Недопустимая роль сотрудника.",
            )

        admin_count = sum(1 for item in get_db().get_all_admins() if item["role"] == "admin")
        if (
            target_admin["role"] == "admin"
            and normalized_role != "admin"
            and admin_count <= 1
        ):
            return _render_staff_page(
                current_admin=admin,
                error="В системе должен остаться хотя бы один администратор.",
            )

        get_db().update_admin_role(admin_id, normalized_role)
        if password.strip():
            get_db().update_admin_password_hash(admin_id, hash_password(password.strip()))

        response = RedirectResponse(url="/admin/staff", status_code=303)
        _set_session_cookie(response, username=admin["username"])
        return response

    @app.exception_handler(404)
    async def not_found_handler(_: Request, __: Any):
        return HTMLResponse(
            views.layout("Not Found", "<h1>404</h1><p>Страница не найдена.</p>"),
            status_code=404,
        )

    return app
