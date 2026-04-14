from __future__ import annotations

import csv
import io
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
            views.dashboard(get_db().get_stats(), get_db().get_all_users()),
            user=admin,
        )

    @app.get("/admin/users", response_class=HTMLResponse)
    async def admin_users(request: Request):
        admin, redirect = require_admin(request)
        if redirect:
            return redirect
        return render_html(views.users_list(get_db().get_all_users()), user=admin)

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
        return render_html(views.user_detail(user, attempts, logs_map), user=admin)

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
        return render_html(views.quests_list(get_db().get_all_quests()), user=admin)

    @app.get("/admin/quests/new", response_class=HTMLResponse)
    async def admin_quest_form(request: Request):
        admin, redirect = require_admin(request)
        if redirect:
            return redirect
        return render_html(views.quest_form(), user=admin)

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
    ):
        admin, redirect = require_admin(request)
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
            views.quest_detail(quest, questions, attempts),
            user=admin,
        )

    @app.get("/admin/quests/{quest_id}/edit", response_class=HTMLResponse)
    async def admin_quest_edit_form(quest_id: int, request: Request):
        admin, redirect = require_admin(request)
        if redirect:
            return redirect
        quest = get_db().get_quest_by_id(quest_id)
        if quest is None:
            return PlainTextResponse("Quest not found", status_code=404)
        return render_html(views.quest_form(dict(quest)), user=admin)

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
    ):
        admin, redirect = require_admin(request)
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
        )
        response = RedirectResponse(url=f"/admin/quests/{quest_id}", status_code=303)
        _set_session_cookie(response, username=admin["username"])
        return response

    @app.post("/admin/quests/{quest_id}/publish")
    async def admin_quest_publish(quest_id: int, request: Request):
        admin, redirect = require_admin(request)
        if redirect:
            return redirect
        get_db().update_quest_status(quest_id, "published")
        response = RedirectResponse(url=f"/admin/quests/{quest_id}", status_code=303)
        _set_session_cookie(response, username=admin["username"])
        return response

    @app.post("/admin/quests/{quest_id}/archive")
    async def admin_quest_archive(quest_id: int, request: Request):
        admin, redirect = require_admin(request)
        if redirect:
            return redirect
        get_db().update_quest_status(quest_id, "archived")
        response = RedirectResponse(url=f"/admin/quests/{quest_id}", status_code=303)
        _set_session_cookie(response, username=admin["username"])
        return response

    @app.post("/admin/quests/{quest_id}/delete")
    async def admin_quest_delete(quest_id: int, request: Request):
        admin, redirect = require_admin(request)
        if redirect:
            return redirect
        if admin["role"] != "admin":
            return PlainTextResponse("Forbidden", status_code=403)
        get_db().delete_quest(quest_id)
        response = RedirectResponse(url="/admin/quests", status_code=303)
        _set_session_cookie(response, username=admin["username"])
        return response

    @app.get("/admin/quests/{quest_id}/questions/new", response_class=HTMLResponse)
    async def admin_question_new_form(quest_id: int, request: Request):
        admin, redirect = require_admin(request)
        if redirect:
            return redirect
        if get_db().get_quest_by_id(quest_id) is None:
            return PlainTextResponse("Quest not found", status_code=404)
        return render_html(views.question_form(quest_id), user=admin)

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
        attempts_override: str = Form(default=""),
    ):
        admin, redirect = require_admin(request)
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
        admin, redirect = require_admin(request)
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
            )
            next_order += 1
        response = RedirectResponse(url=f"/admin/quests/{quest_id}", status_code=303)
        _set_session_cookie(response, username=admin["username"])
        return response

    @app.get("/admin/questions/{question_id}/edit", response_class=HTMLResponse)
    async def admin_question_edit_form(question_id: int, request: Request):
        admin, redirect = require_admin(request)
        if redirect:
            return redirect
        question = get_db().get_question_by_id(question_id)
        if question is None:
            return PlainTextResponse("Question not found", status_code=404)
        return render_html(
            views.question_form(_quest_id_from_question(question), dict(question)),
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
        attempts_override: str = Form(default=""),
    ):
        admin, redirect = require_admin(request)
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
        admin, redirect = require_admin(request)
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
    async def admin_attempt_gift(attempt_id: int, request: Request):
        admin, redirect = require_admin(request)
        if redirect:
            return redirect
        attempt = get_db().get_attempt_by_id(attempt_id)
        if attempt is None or attempt["status"] != "completed":
            return PlainTextResponse("Attempt not found", status_code=404)
        get_db().mark_gift_given(attempt_id, admin["id"])
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
        return render_html(views.stats_page(get_db().get_stats()), user=admin)

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

    @app.exception_handler(404)
    async def not_found_handler(_: Request, __: Any):
        return HTMLResponse(
            views.layout("Not Found", "<h1>404</h1><p>Страница не найдена.</p>"),
            status_code=404,
        )

    return app
