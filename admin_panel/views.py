import html


def _escape(value):
    if value is None:
        return ""
    return html.escape(str(value))


def _is_admin(user) -> bool:
    if not user:
        return False
    try:
        return user["role"] == "admin"
    except Exception:
        return False


def _role_label(role: str) -> str:
    return "Администратор" if role == "admin" else "Оператор"


def _badge(text: str, kind: str) -> str:
    return f'<span class="badge badge-{kind}">{_escape(text)}</span>'


def _checked_attr(value) -> str:
    return " checked" if value else ""


def _datetime_local_value(raw_value) -> str:
    if not raw_value:
        return ""
    return str(raw_value).replace(" ", "T")[:16]


def _cell(label: str, value: str, class_name: str = "") -> str:
    cls = f' class="{class_name}"' if class_name else ""
    return f'<td data-label="{_escape(label)}"{cls}>{value}</td>'


def _full_row(content: str, colspan: int, class_name: str = "") -> str:
    extra = f" {class_name}" if class_name else ""
    return f'<tr class="full-row{extra}"><td colspan="{colspan}">{content}</td></tr>'


def _table(headers: list[str], rows: str, empty_message: str, colspan: int | None = None) -> str:
    if not rows:
        rows = _full_row(f'<div class="empty">{_escape(empty_message)}</div>', colspan or len(headers))
    head = "".join(f"<th>{_escape(header)}</th>" for header in headers)
    return (
        '<table class="responsive-table">'
        f"<thead><tr>{head}</tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table>"
    )


def layout(title, body, user=None, active=""):
    nav = ""
    if user:
        items = [
            ("dashboard", "📊 Dashboard", "/admin/dashboard"),
            ("users", "👥 Пользователи", "/admin/users"),
            ("quests", "🗺️ Квесты", "/admin/quests"),
            ("stats", "📈 Статистика", "/admin/stats"),
            ("export", "📥 Экспорт CSV", "/admin/export"),
        ]
        if _is_admin(user):
            items.append(("staff", "🛡️ Сотрудники", "/admin/staff"))

        links = []
        for key, label, href in items:
            cls = ' class="active"' if key == active else ""
            links.append(f'<a href="{href}"{cls}>{label}</a>')
        links.append(
            f'<a href="/admin/logout">🚪 Выйти ({_escape(user["username"])}, {_escape(_role_label(user["role"]))})</a>'
        )
        nav = '<nav class="sidebar">' + "".join(links) + "</nav>"

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_escape(title)} — MaxQuestBot</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f6fa;color:#2d3436;display:flex;min-height:100vh}}
.sidebar{{width:220px;background:#2d3436;color:#fff;padding:20px 0;position:fixed;top:0;left:0;bottom:0;overflow-y:auto}}
.sidebar a{{display:block;padding:12px 20px;color:#dfe6e9;text-decoration:none;font-size:14px;transition:background .2s}}
.sidebar a:hover,.sidebar a.active{{background:#636e72;color:#fff}}
.content{{margin-left:220px;padding:30px;flex:1;max-width:1180px}}
h1{{font-size:24px;margin-bottom:20px}}
h2{{font-size:20px;margin:20px 0 10px}}
h3{{font-size:16px;margin-bottom:10px}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.1)}}
th,td{{padding:10px 14px;text-align:left;border-bottom:1px solid #eee;font-size:14px;vertical-align:top}}
th{{background:#636e72;color:#fff;font-weight:600}}
tr:hover{{background:#f8f9fa}}
.responsive-table .full-row td{{padding:0;border-bottom:none}}
.badge{{display:inline-block;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600}}
.badge-green{{background:#00b894;color:#fff}}
.badge-yellow{{background:#fdcb6e;color:#2d3436}}
.badge-red{{background:#e17055;color:#fff}}
.badge-blue{{background:#74b9ff;color:#2d3436}}
.btn{{display:inline-block;padding:8px 16px;border:none;border-radius:6px;cursor:pointer;font-size:14px;text-decoration:none;color:#fff;transition:opacity .2s}}
.btn:hover{{opacity:.85}}
.btn-primary{{background:#6c5ce7}}
.btn-success{{background:#00b894}}
.btn-danger{{background:#e17055}}
.btn-secondary{{background:#636e72}}
.btn-sm{{padding:5px 10px;font-size:12px}}
form{{background:#fff;padding:20px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.1);max-width:720px}}
.form-group{{margin-bottom:16px}}
.form-group label{{display:block;margin-bottom:4px;font-weight:600;font-size:14px}}
.form-group input,.form-group textarea,.form-group select{{width:100%;padding:8px 12px;border:1px solid #ddd;border-radius:6px;font-size:14px}}
.form-group textarea{{min-height:80px;resize:vertical}}
.checkbox-row{{display:flex;align-items:center;gap:8px}}
.checkbox-row input{{width:auto}}
.actions{{margin:16px 0}}
.actions a,.actions button{{margin-right:8px}}
.card{{background:#fff;padding:20px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.1);margin-bottom:16px}}
.card-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}}
.card p{{margin-bottom:8px}}
.stats-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px;margin-bottom:24px}}
.stat-card{{background:#fff;padding:20px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.1);text-align:center}}
.stat-card .num{{font-size:32px;font-weight:700;color:#6c5ce7}}
.stat-card .label{{font-size:14px;color:#636e72;margin-top:4px}}
.login-box{{max-width:360px;margin:80px auto;background:#fff;padding:40px;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,.1)}}
.login-box h1{{text-align:center;margin-bottom:24px}}
.error{{background:#ffeaa7;padding:10px;border-radius:6px;margin-bottom:16px;color:#d63031}}
.success{{background:#dff8eb;padding:10px;border-radius:6px;margin-bottom:16px;color:#0f7a47}}
.back-link{{margin-bottom:16px;display:inline-block;color:#6c5ce7;text-decoration:none}}
.empty{{padding:20px;text-align:center;color:#636e72;font-style:italic}}
.inline-form{{display:flex;gap:8px;align-items:center;flex-wrap:wrap;background:transparent;padding:0;box-shadow:none;max-width:none}}
.inline-form input,.inline-form select{{width:auto;min-width:120px}}
.muted{{color:#636e72;font-size:12px}}
details summary{{cursor:pointer;color:#636e72}}
code{{background:#f1f2f6;padding:2px 4px;border-radius:4px}}
@media (max-width: 900px){{
body{{display:block;min-height:auto}}
.sidebar{{position:static;width:100%;display:flex;gap:8px;padding:10px;overflow-x:auto;overflow-y:hidden;white-space:nowrap}}
.sidebar a{{flex:0 0 auto;padding:10px 14px;border-radius:8px;background:rgba(255,255,255,.06)}}
.content{{margin-left:0;padding:16px;max-width:none;width:100%}}
.stats-grid,.card-grid{{grid-template-columns:1fr}}
.actions{{display:flex;flex-direction:column;align-items:stretch;gap:8px}}
.actions a,.actions button,.actions form{{margin-right:0;width:100%}}
form{{max-width:none}}
.inline-form{{flex-direction:column;align-items:stretch}}
.inline-form input,.inline-form select,.inline-form button{{width:100%;min-width:0}}
.login-box{{max-width:none;margin:24px auto;padding:24px}}
table.responsive-table{{display:block;background:transparent;box-shadow:none;border-radius:0;overflow:visible;white-space:normal}}
table.responsive-table thead{{display:none}}
table.responsive-table tbody{{display:block}}
table.responsive-table tr{{display:block;background:#fff;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,.1);margin-bottom:12px;padding:8px 0}}
table.responsive-table tr.full-row{{padding:0;background:transparent;box-shadow:none}}
table.responsive-table td{{display:block;padding:10px 12px;border-bottom:1px solid #eee;white-space:normal;word-break:break-word}}
table.responsive-table td::before{{content:attr(data-label);display:block;margin-bottom:4px;font-size:12px;font-weight:600;color:#636e72}}
table.responsive-table tr td:last-child{{border-bottom:none}}
table.responsive-table tr.full-row td{{padding:0;border-bottom:none}}
table.responsive-table tr.full-row td::before{{display:none;content:none}}
}}
</style>
</head>
<body>
{nav}
<div class="content">
{body}
</div>
</body>
</html>"""


def login_page(error=""):
    err = f'<div class="error">{_escape(error)}</div>' if error else ""
    body = f"""<div class="login-box">
<h1>🔐 MaxQuestBot</h1>
{err}
<form method="POST" action="/admin/login">
<div class="form-group"><label>Логин</label><input type="text" name="username" required autofocus></div>
<div class="form-group"><label>Пароль</label><input type="password" name="password" required></div>
<button class="btn btn-primary" style="width:100%">Войти</button>
</form>
</div>"""
    return layout("Вход", body)


def _users_table(users):
    rows = ""
    for user in users:
        uid = user["id"]
        consent = "✅" if user["consent_given"] else "❌"
        user_link = f"<a href='/admin/users/{uid}'>{_escape(user['max_user_id'])}</a>"
        rows += (
            f"<tr>"
            f"{_cell('ID', str(uid))}"
            f"{_cell('MAX ID', user_link)}"
            f"{_cell('Телефон', _escape(user['phone'] or '—'))}"
            f"{_cell('Квестов пройдено', str(int(user['completed_quests_count'] or 0)))}"
            f"{_cell('Согласие', consent)}"
            f"{_cell('Дата регистрации', _escape(user['registered_at'] or ''))}"
            f"</tr>"
        )
    return _table(
        ["ID", "MAX ID", "Телефон", "Квестов пройдено", "Согласие", "Дата регистрации"],
        rows,
        "Нет пользователей",
    )


def dashboard(stats, users, user=None):
    cards = ""
    items = [
        (stats["total_users"], "Пользователей"),
        (stats["total_quests"], "Квестов"),
        (stats["published_quests"], "Опубликованных"),
        (stats["active_attempts"], "Активных прохождений"),
        (stats["completed_attempts"], "Завершённых"),
        (stats["gifts_given"], "Подарков выдано"),
    ]
    for num, label in items:
        cards += f'<div class="stat-card"><div class="num">{num}</div><div class="label">{label}</div></div>'
    body = (
        "<h1>📊 Dashboard</h1>"
        f"<div class='stats-grid'>{cards}</div>"
        "<div class='card'>"
        "<h2>👥 Авторизованные пользователи</h2>"
        f"{_users_table(users)}"
        "</div>"
    )
    return layout("Dashboard", body, user=user, active="dashboard")


def users_list(users, user=None):
    body = f"<h1>👥 Пользователи</h1>{_users_table(users)}"
    return layout("Пользователи", body, user=user, active="users")


def user_detail(user, attempts, answer_logs_map, current_admin):
    uid = user["id"]
    body = f"""<h1>👤 Пользователь #{uid}</h1>
<div class="card-grid">
<div class="card">
<h3>Информация</h3>
<p><strong>MAX ID:</strong> {_escape(user['max_user_id'])}</p>
<p><strong>Телефон:</strong> {_escape(user['phone'] or '—')}</p>
<p><strong>Согласие:</strong> {'✅ Дано' if user['consent_given'] else '❌ Не дано'}</p>
<p><strong>Дата регистрации:</strong> {_escape(user['registered_at'] or '')}</p>
</div>
<div class="card">
<h3>Комментарий</h3>
<form method="POST" action="/admin/users/{uid}/comment">
<div class="form-group"><textarea name="comment">{_escape(user['comment'] or '')}</textarea></div>
<button class="btn btn-primary btn-sm">Сохранить</button>
</form>
</div>
</div>

<h2>🎯 Прохождения квестов</h2>"""

    if not attempts:
        body += '<p class="empty">Нет прохождений</p>'
    else:
        attempt_rows = ""
        for attempt in attempts:
            status_badge = (
                _badge("В процессе", "blue")
                if attempt["status"] == "in_progress"
                else _badge("Завершён", "green")
            )

            gift_info = "—"
            actions = ""
            if attempt["status"] == "completed":
                if attempt["gift_given"]:
                    issuer = attempt["gift_given_by_username"] or "—"
                    gift_info = (
                        f"{_badge('✅ Выдан', 'green')}<br>"
                        f"<small>{_escape(attempt['gift_given_at'] or '')}</small><br>"
                        f"<small>Отметил: {_escape(issuer)}</small>"
                    )
                else:
                    gift_info = _badge("Не выдан", "yellow")
                    actions = f"""
<form method="POST" action="/admin/attempts/{attempt['id']}/gift" class="inline-form">
<input type="datetime-local" name="gift_given_at" value="">
<input type="text" name="comment" value="{_escape(attempt['comment'] or '')}" placeholder="Комментарий">
<button class="btn btn-success btn-sm">🎁 Выдать</button>
</form>"""

            if not actions:
                actions = '<span class="muted">Доп. действий нет</span>'

            comment_value = attempt["comment"] or ""
            attempt_rows += (
                "<tr>"
                f"{_cell('Квест', _escape(attempt['quest_name']))}"
                f"{_cell('Статус', status_badge)}"
                f"{_cell('Начат', _escape(attempt['started_at'] or ''))}"
                f"{_cell('Завершён', _escape(attempt['completed_at'] or '—'))}"
                f"{_cell('Подарок', gift_info)}"
                f"{_cell('Действия', actions)}"
                "</tr>"
            )

            logs = answer_logs_map.get(attempt["id"], [])
            if logs:
                log_rows = ""
                for log in logs:
                    mark = "✅" if log["is_correct"] else "❌"
                    log_rows += (
                        "<tr>"
                        f"{_cell('Статус', mark)}"
                        f"{_cell('Вопрос', _escape(log['task_text']))}"
                        f"{_cell('Ответ', _escape(log['answer_text']))}"
                        f"{_cell('Эталон', _escape(log['correct_answer']))}"
                        f"{_cell('Время', _escape(log['answered_at'] or ''))}"
                        "</tr>"
                    )
                logs_table = _table(
                    ["Статус", "Вопрос", "Ответ", "Эталон", "Время"],
                    log_rows,
                    "Нет логов ответов",
                )
                attempt_rows += _full_row(
                    '<details><summary style="padding:8px 14px">📋 Логи ответов</summary>'
                    f"{logs_table}</details>",
                    6,
                )

            attempt_rows += _full_row(
                f"<form method='POST' action='/admin/attempts/{attempt['id']}/comment' class='inline-form'>"
                f"<input type='text' name='comment' value='{_escape(comment_value)}' placeholder='Комментарий по прохождению' style='flex:1'>"
                "<button class='btn btn-secondary btn-sm'>💾 Сохранить комментарий</button>"
                "</form>",
                6,
            )
        body += _table(
            ["Квест", "Статус", "Начат", "Завершён", "Подарок", "Действия"],
            attempt_rows,
            "Нет прохождений",
        )

    return layout(f"Пользователь #{uid}", body, user=current_admin, active="users")


def quests_list(quests, user=None):
    rows = ""
    for quest in quests:
        qid = quest["id"]
        status_map = {
            "draft": _badge("Черновик", "yellow"),
            "published": _badge("Опубликован", "green"),
            "archived": _badge("Архив", "red"),
        }
        quest_link = f"<a href='/admin/quests/{qid}'>{_escape(quest['name'])}</a>"
        open_button = f"<a href='/admin/quests/{qid}' class='btn btn-primary btn-sm'>Открыть</a>"
        rows += (
            "<tr>"
            f"{_cell('ID', str(qid))}"
            f"{_cell('Название', quest_link)}"
            f"{_cell('Статус', status_map.get(quest['status'], _escape(quest['status'])))}"
            f"{_cell('Начало', _escape(quest['start_date'] or '—'))}"
            f"{_cell('Конец', _escape(quest['end_date'] or '—'))}"
            f"{_cell('Попыток', str(quest['max_attempts']))}"
            f"{_cell('Повтор до подарка', 'Да' if quest['allow_retry_before_gift'] else 'Нет')}"
            f"{_cell('Действия', open_button)}"
            "</tr>"
        )

    create_button = ""
    import_button = ""
    if _is_admin(user):
        create_button = '<a href="/admin/quests/new" class="btn btn-primary">+ Создать квест</a>'
        import_button = '<a href="/admin/quests/import" class="btn btn-secondary">📥 Импортировать квест из CSV</a>'

    body = f"""<h1>🗺️ Квесты</h1>
<div class="actions">{create_button}{import_button}</div>
<div style="margin-top:16px">{_table(["ID", "Название", "Статус", "Начало", "Конец", "Попыток", "Повтор до подарка", "Действия"], rows, "Нет квестов")}</div>"""
    return layout("Квесты", body, user=user, active="quests")


def quest_form(quest=None, error="", user=None):
    is_edit = quest is not None
    title = "Редактирование квеста" if is_edit else "Новый квест"
    action = f"/admin/quests/{quest['id']}" if is_edit else "/admin/quests"
    values = quest or {}
    err = f'<div class="error">{_escape(error)}</div>' if error else ""
    body = f"""<h1>{title}</h1>
<a href="/admin/quests" class="back-link">← Назад к списку</a>
{err}
<form method="POST" action="{action}">
<div class="form-group"><label>Название</label><input name="name" value="{_escape(values.get('name', ''))}" required></div>
<div class="form-group"><label>Описание</label><textarea name="description">{_escape(values.get('description', ''))}</textarea></div>
<div class="form-group"><label>Точка начала</label><input name="start_point" value="{_escape(values.get('start_point', ''))}"></div>
<div class="form-group"><label>Место получения приза</label><input name="prize_location" value="{_escape(values.get('prize_location', ''))}"></div>
<div class="form-group"><label>Дата начала</label><input type="date" name="start_date" value="{_escape(values.get('start_date', '') or '')}"></div>
<div class="form-group"><label>Дата окончания</label><input type="date" name="end_date" value="{_escape(values.get('end_date', '') or '')}"></div>
<div class="form-group"><label>Попыток на вопрос (0 = без ограничений)</label><input type="number" name="max_attempts" value="{values.get('max_attempts', 3)}" min="0"></div>
<div class="form-group">
<label class="checkbox-row">
<input type="checkbox" name="allow_retry_before_gift"{_checked_attr(values.get('allow_retry_before_gift'))}>
<span>Разрешить повторное прохождение до выдачи подарка</span>
</label>
<div class="muted">Если выключено, после завершения квеста повторный запуск запрещён до решения сотрудника.</div>
</div>
<button class="btn btn-primary">Сохранить</button>
</form>"""
    return layout(title, body, user=user, active="quests")


def quest_import_form(*, name: str = "", errors: list[str] | None = None, user=None):
    error_block = ""
    if errors:
        error_items = "".join(f"<li>{_escape(error)}</li>" for error in errors)
        error_block = f"<div class='error'><ul>{error_items}</ul></div>"

    expected_header = "question_order,context,question_text,correct_answer,hint,answer_explanation"
    body = f"""<h1>📥 Импорт квеста из CSV</h1>
<a href="/admin/quests" class="back-link">← Назад к списку</a>
{error_block}
<form method="POST" action="/admin/quests/import" enctype="multipart/form-data">
<div class="form-group"><label>Название квеста</label><input name="name" value="{_escape(name)}" required></div>
<div class="form-group"><label>CSV-файл</label><input type="file" name="csv_file" accept=".csv" required></div>
<div class="muted">Ожидаемый заголовок CSV: <code>{_escape(expected_header)}</code></div>
<button class="btn btn-primary">Загрузить</button>
</form>"""
    return layout("Импорт квеста", body, user=user, active="quests")


def quest_detail(quest, questions, attempts, user=None, notice: str = ""):
    qid = quest["id"]
    status_map = {
        "draft": _badge("Черновик", "yellow"),
        "published": _badge("Опубликован", "green"),
        "archived": _badge("Архив", "red"),
    }
    controls = ""
    publish_button = ""
    if _is_admin(user):
        controls += f'<a href="/admin/quests/{qid}/edit" class="btn btn-primary">✏️ Редактировать</a>'
        if quest["status"] == "draft":
            publish_button = (
                f'<form method="POST" action="/admin/quests/{qid}/publish" class="inline-form">'
                '<button class="btn btn-success">Опубликовать</button></form>'
            )
        elif quest["status"] == "published":
            publish_button = (
                f'<form method="POST" action="/admin/quests/{qid}/archive" class="inline-form">'
                '<button class="btn btn-secondary">В архив</button></form>'
            )
        controls += publish_button
        controls += (
            f"<form method='POST' action='/admin/quests/{qid}/delete' class='inline-form' "
            "onsubmit=\"return confirm('Удалить квест и все вопросы?')\">"
            "<button class='btn btn-danger'>🗑️ Удалить</button></form>"
        )

    question_rows = ""
    for question in questions:
        actions = '<span class="muted">Только просмотр</span>'
        if _is_admin(user):
            actions = (
                f"<a href='/admin/questions/{question['id']}/edit' class='btn btn-primary btn-sm'>✏️</a> "
                f"<form method='POST' action='/admin/questions/{question['id']}/delete' class='inline-form'>"
                "<button class='btn btn-danger btn-sm' onclick='return confirm(\"Удалить?\")'>🗑️</button></form>"
            )
        question_rows += (
            "<tr>"
            f"{_cell('№', str(question['order_num']))}"
            f"{_cell('Задание', _escape(question['task_text']))}"
            f"{_cell('Ответ', _escape(question['correct_answer']))}"
            f"{_cell('Режим', _escape(question['semantic_mode'] or 'simple'))}"
            f"{_cell('Порог', _escape(question['semantic_threshold']))}"
            f"{_cell('Попытки', _escape(question['attempts_override'] or 'из квеста'))}"
            f"{_cell('Действия', actions)}"
            "</tr>"
        )

    attempt_rows = ""
    for attempt in attempts:
        gift_state = "✅"
        if not attempt["gift_given"]:
            gift_state = "❌"
        if attempt["gift_given"] and attempt["gift_given_by_username"]:
            gift_state = (
                f"✅<br><small>{_escape(attempt['gift_given_at'] or '')}</small><br>"
                f"<small>{_escape(attempt['gift_given_by_username'])}</small>"
            )
        attempt_rows += (
            "<tr>"
            f"{_cell('MAX ID', _escape(attempt['max_user_id']))}"
            f"{_cell('Телефон', _escape(attempt['phone'] or '—'))}"
            f"{_cell('Статус', 'Завершён' if attempt['status'] == 'completed' else 'В процессе')}"
            f"{_cell('Подарок', gift_state)}"
            f"{_cell('Дата старта', _escape(attempt['started_at'] or ''))}"
            "</tr>"
        )

    notice_html = ""
    if notice:
        notice_html = f"<div class='success'>{_escape(notice)}</div>"

    question_tools = ""
    if _is_admin(user):
        question_tools = (
            f'<a href="/admin/quests/{qid}/questions/new" class="btn btn-primary btn-sm">+ Добавить вопрос</a>'
        )

    body = f"""<h1>🗺️ {_escape(quest['name'])}</h1>
<a href="/admin/quests" class="back-link">← Назад к списку</a>
{notice_html}
<div class="card">
<h3>Информация</h3>
<p><strong>Статус:</strong> {status_map.get(quest['status'], _escape(quest['status']))}</p>
<p><strong>Описание:</strong> {_escape(quest['description'] or '—')}</p>
<p><strong>Точка начала:</strong> {_escape(quest['start_point'] or '—')}</p>
<p><strong>Инструкция по призу:</strong> {_escape(quest['prize_location'] or '—')}</p>
<p><strong>Даты:</strong> {_escape(quest['start_date'] or '∞')} — {_escape(quest['end_date'] or '∞')}</p>
<p><strong>Попыток на вопрос:</strong> {quest['max_attempts']}</p>
<p><strong>Повтор до подарка:</strong> {'Да' if quest['allow_retry_before_gift'] else 'Нет'}</p>
</div>
<div class="actions">{controls}</div>

<h2>❓ Вопросы ({len(questions)})</h2>
<div class="actions">{question_tools}</div>
{_table(["№", "Задание", "Ответ", "Режим", "Порог", "Попытки", "Действия"], question_rows, "Нет вопросов")}

<h2>👥 Прохождения ({len(attempts)})</h2>
{_table(["MAX ID", "Телефон", "Статус", "Подарок", "Дата старта"], attempt_rows, "Нет прохождений")}"""
    return layout(quest["name"], body, user=user, active="quests")


def question_form(quest_id, question=None, user=None):
    is_edit = question is not None
    title = "Редактирование вопроса" if is_edit else "Новый вопрос"
    action = f"/admin/questions/{question['id']}" if is_edit else f"/admin/quests/{quest_id}/questions"
    values = question or {}
    body = f"""<h1>{title}</h1>
<a href="/admin/quests/{quest_id}" class="back-link">← Назад к квесту</a>
<form method="POST" action="{action}">
<div class="form-group"><label>Порядковый номер</label><input type="number" name="order_num" value="{values.get('order_num', 1)}" min="1" required></div>
<div class="form-group"><label>Справка / контекст</label><textarea name="context">{_escape(values.get('context', ''))}</textarea></div>
<div class="form-group"><label>Задание</label><textarea name="task_text" required>{_escape(values.get('task_text', ''))}</textarea></div>
<div class="form-group"><label>Правильный ответ</label><input name="correct_answer" value="{_escape(values.get('correct_answer', ''))}" required></div>
<div class="form-group"><label>Пояснение</label><textarea name="explanation">{_escape(values.get('explanation', ''))}</textarea></div>
<div class="form-group"><label>Подсказка</label><textarea name="hint">{_escape(values.get('hint', ''))}</textarea></div>
<div class="form-group">
<label>Режим проверки по смыслу</label>
<select name="semantic_mode">
<option value="simple"{' selected' if values.get('semantic_mode', 'simple') == 'simple' else ''}>simple</option>
<option value="contains"{' selected' if values.get('semantic_mode') == 'contains' else ''}>contains</option>
<option value="exact"{' selected' if values.get('semantic_mode') == 'exact' else ''}>exact</option>
</select>
<div class="muted">simple = мягкое сравнение, contains = вхождение / слова, exact = только точное совпадение.</div>
</div>
<div class="form-group"><label>Порог семантического совпадения</label><input type="number" name="semantic_threshold" min="0" max="1" step="0.05" value="{values.get('semantic_threshold', 0.6)}"></div>
<div class="form-group"><label>Попыток (переопределение, пусто = из квеста)</label><input type="number" name="attempts_override" value="{values.get('attempts_override') or ''}" min="0"></div>
<button class="btn btn-primary">Сохранить</button>
</form>"""
    return layout(title, body, user=user, active="quests")


def stats_page(stats, user=None):
    body = f"""<h1>📈 Статистика</h1>
<div class="stats-grid">
<div class="stat-card"><div class="num">{stats['total_users']}</div><div class="label">Пользователей</div></div>
<div class="stat-card"><div class="num">{stats['total_quests']}</div><div class="label">Квестов всего</div></div>
<div class="stat-card"><div class="num">{stats['published_quests']}</div><div class="label">Опубликованных</div></div>
<div class="stat-card"><div class="num">{stats['completed_attempts']}</div><div class="label">Завершённых прохождений</div></div>
<div class="stat-card"><div class="num">{stats['active_attempts']}</div><div class="label">Активных прохождений</div></div>
<div class="stat-card"><div class="num">{stats['gifts_given']}</div><div class="label">Подарков выдано</div></div>
</div>"""
    return layout("Статистика", body, user=user, active="stats")


def staff_page(admins, current_admin, error=""):
    rows = ""
    for admin in admins:
        role_options = []
        for role in ("admin", "operator"):
            selected = " selected" if admin["role"] == role else ""
            role_options.append(
                f"<option value='{role}'{selected}>{_escape(_role_label(role))}</option>"
            )
        manage_form = (
            f"<form method='POST' action='/admin/staff/{admin['id']}' class='inline-form'>"
            f"<select name='role'>{''.join(role_options)}</select>"
            "<input type='password' name='password' placeholder='Новый пароль'>"
            "<button class='btn btn-primary btn-sm'>Сохранить</button>"
            "</form>"
        )
        rows += (
            "<tr>"
            f"{_cell('ID', str(admin['id']))}"
            f"{_cell('Логин', _escape(admin['username']))}"
            f"{_cell('Роль', _escape(_role_label(admin['role'])))}"
            f"{_cell('Создан', _escape(admin['created_at'] or ''))}"
            f"{_cell('Управление', manage_form)}"
            "</tr>"
        )

    err = f'<div class="error">{_escape(error)}</div>' if error else ""
    body = f"""<h1>🛡️ Сотрудники</h1>
{err}
<div class="card">
<h3>Новый сотрудник</h3>
<form method="POST" action="/admin/staff">
<div class="form-group"><label>Логин</label><input name="username" required></div>
<div class="form-group"><label>Пароль</label><input type="password" name="password" required></div>
<div class="form-group"><label>Роль</label>
<select name="role">
<option value="operator">Оператор</option>
<option value="admin">Администратор</option>
</select></div>
<button class="btn btn-primary">Создать сотрудника</button>
</form>
</div>
<h2>Текущая команда</h2>
{_table(["ID", "Логин", "Роль", "Создан", "Управление"], rows, "Нет сотрудников")}"""
    return layout("Сотрудники", body, user=current_admin, active="staff")
