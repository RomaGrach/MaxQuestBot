import html
import urllib.parse


def _escape(s):
    if s is None:
        return ""
    return html.escape(str(s))


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
        links = []
        for key, label, href in items:
            cls = ' class="active"' if key == active else ""
            links.append(f'<a href="{href}"{cls}>{label}</a>')
        nav = (
            '<nav class="sidebar">'
            + "".join(links)
            + f'<a href="/admin/logout">🚪 Выйти ({_escape(user["username"])})</a>'
            + "</nav>"
        )
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
.content{{margin-left:220px;padding:30px;flex:1;max-width:960px}}
h1{{font-size:24px;margin-bottom:20px}}
h2{{font-size:20px;margin:20px 0 10px}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.1)}}
th,td{{padding:10px 14px;text-align:left;border-bottom:1px solid #eee;font-size:14px}}
th{{background:#636e72;color:#fff;font-weight:600}}
tr:hover{{background:#f8f9fa}}
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
form{{background:#fff;padding:20px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.1);max-width:600px}}
.form-group{{margin-bottom:16px}}
.form-group label{{display:block;margin-bottom:4px;font-weight:600;font-size:14px}}
.form-group input,.form-group textarea,.form-group select{{width:100%;padding:8px 12px;border:1px solid #ddd;border-radius:6px;font-size:14px}}
.form-group textarea{{min-height:80px;resize:vertical}}
.actions{{margin-top:16px}}
.actions a,.actions button{{margin-right:8px}}
.card{{background:#fff;padding:20px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.1);margin-bottom:16px}}
.card h3{{margin-bottom:10px;font-size:16px}}
.stats-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px;margin-bottom:24px}}
.stat-card{{background:#fff;padding:20px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.1);text-align:center}}
.stat-card .num{{font-size:32px;font-weight:700;color:#6c5ce7}}
.stat-card .label{{font-size:14px;color:#636e72;margin-top:4px}}
.login-box{{max-width:360px;margin:80px auto;background:#fff;padding:40px;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,.1)}}
.login-box h1{{text-align:center;margin-bottom:24px}}
.error{{background:#ffeaa7;padding:10px;border-radius:6px;margin-bottom:16px;color:#d63031}}
.success{{background:#55efc4;padding:10px;border-radius:6px;margin-bottom:16px;color:#00b894}}
.back-link{{margin-bottom:16px;display:inline-block;color:#6c5ce7;text-decoration:none}}
.empty{{padding:20px;text-align:center;color:#636e72;font-style:italic}}
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
    for u in users:
        uid = u["id"]
        consent = "✅" if u["consent_given"] else "❌"
        rows += (
            f"<tr>"
            f"<td>{uid}</td>"
            f"<td><a href='/admin/users/{uid}'>{_escape(u['max_user_id'])}</a></td>"
            f"<td>{_escape(u['phone'] or '—')}</td>"
            f"<td>{int(u['completed_quests_count'] or 0)}</td>"
            f"<td>{consent}</td>"
            f"<td>{_escape(u['registered_at'] or '')}</td>"
            f"</tr>"
        )
    if not rows:
        rows = '<tr><td colspan="6" class="empty">Нет пользователей</td></tr>'
    return (
        "<table><tr><th>ID</th><th>MAX ID</th><th>Телефон</th><th>Квестов пройдено</th><th>Согласие</th><th>Дата регистрации</th></tr>"
        f"{rows}</table>"
    )


def dashboard(stats, users):
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
    users_table = _users_table(users)
    body = (
        f"<h1>📊 Dashboard</h1>"
        f"<div class='stats-grid'>{cards}</div>"
        f"<div class='card'>"
        f"<h2>👥 Авторизованные пользователи</h2>"
        f"{users_table}"
        f"</div>"
    )
    return layout("Dashboard", body, active="dashboard")


def users_list(users):
    body = f"""<h1>👥 Пользователи</h1>
{_users_table(users)}"""
    return layout("Пользователи", body, active="users")


def user_detail(user, attempts, answer_logs_map):
    uid = user["id"]
    body = f"""<h1>👤 Пользователь #{uid}</h1>
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

<h2>🎯 Прохождения квестов</h2>"""

    if not attempts:
        body += '<p class="empty">Нет прохождений</p>'
    else:
        body += "<table><tr><th>Квест</th><th>Статус</th><th>Начат</th><th>Завершён</th><th>Подарок</th><th>Действия</th></tr>"
        for a in attempts:
            status_badge = (
                '<span class="badge badge-blue">В процессе</span>'
                if a["status"] == "in_progress"
                else '<span class="badge badge-green">Завершён</span>'
            )
            gift_text = "—"
            gift_btn = ""
            if a["status"] == "completed":
                if a["gift_given"]:
                    gift_text = f'<span class="badge badge-green">✅ Выдан</span><br><small>{_escape(a["gift_given_at"] or "")}</small>'
                else:
                    gift_text = '<span class="badge badge-yellow">Не выдан</span>'
                    gift_btn = f'<form method="POST" action="/admin/attempts/{a["id"]}/gift" style="display:inline"><button class="btn btn-success btn-sm">🎁 Выдать</button></form>'

            body += (
                f"<tr>"
                f"<td>{_escape(a['quest_name'])}</td>"
                f"<td>{status_badge}</td>"
                f"<td>{_escape(a['started_at'] or '')}</td>"
                f"<td>{_escape(a['completed_at'] or '—')}</td>"
                f"<td>{gift_text}</td>"
                f"<td>{gift_btn}</td>"
                f"</tr>"
            )

            logs = answer_logs_map.get(a["id"], [])
            if logs:
                body += '<tr><td colspan="6" style="padding:0"><details><summary style="padding:8px 14px;cursor:pointer;font-size:13px;color:#636e72">📋 Логи ответов</summary><table style="margin:0;border:none">'
                for log in logs:
                    mark = "✅" if log["is_correct"] else "❌"
                    body += (
                        f"<tr><td>{mark}</td>"
                        f"<td>{_escape(log['task_text'][:60])}...</td>"
                        f"<td>{_escape(log['answer_text'])}</td>"
                        f"<td>{_escape(log['correct_answer'])}</td>"
                        f"<td>{_escape(log['answered_at'] or '')}</td></tr>"
                    )
                body += "</table></details></td></tr>"

            body += (
                f'<tr><td colspan="6"><form method="POST" action="/admin/attempts/{a["id"]}/comment" '
                f'style="display:flex;gap:8px;align-items:center;padding:6px 14px">'
                f'<input type="text" name="comment" value="{_escape(a["comment"] or "")}" '
                f'placeholder="Комментарий" style="flex:1;padding:4px 8px;border:1px solid #ddd;border-radius:4px">'
                f'<button class="btn btn-secondary btn-sm">💾</button></form></td></tr>'
            )

        body += "</table>"

    return layout(f"Пользователь #{uid}", body, active="users")


def quests_list(quests):
    rows = ""
    for q in quests:
        qid = q["id"]
        status_map = {
            "draft": '<span class="badge badge-yellow">Черновик</span>',
            "published": '<span class="badge badge-green">Опубликован</span>',
            "archived": '<span class="badge badge-red">Архив</span>',
        }
        st = status_map.get(q["status"], q["status"])
        rows += (
            f"<tr>"
            f"<td>{qid}</td>"
            f"<td><a href='/admin/quests/{qid}'>{_escape(q['name'])}</a></td>"
            f"<td>{st}</td>"
            f"<td>{_escape(q['start_date'] or '—')}</td>"
            f"<td>{_escape(q['end_date'] or '—')}</td>"
            f"<td>{q['max_attempts']}</td>"
            f"<td>"
            f"<a href='/admin/quests/{qid}' class='btn btn-primary btn-sm'>Открыть</a> "
            f"</td></tr>"
        )
    if not rows:
        rows = '<tr><td colspan="7" class="empty">Нет квестов</td></tr>'
    body = f"""<h1>🗺️ Квесты</h1>
<a href="/admin/quests/new" class="btn btn-primary">+ Создать квест</a>
<table style="margin-top:16px"><tr>
<th>ID</th><th>Название</th><th>Статус</th><th>Начало</th><th>Конец</th><th>Попыток</th><th></th></tr>
{rows}</table>"""
    return layout("Квесты", body, active="quests")


def quest_form(quest=None, error=""):
    is_edit = quest is not None
    title = "Редактирование квеста" if is_edit else "Новый квест"
    action = f"/admin/quests/{quest['id']}" if is_edit else "/admin/quests"
    v = quest or {}
    err = f'<div class="error">{_escape(error)}</div>' if error else ""
    body = f"""<h1>{title}</h1>
<a href="/admin/quests" class="back-link">← Назад к списку</a>
{err}
<form method="POST" action="{action}">
<div class="form-group"><label>Название</label><input name="name" value="{_escape(v.get('name',''))}" required></div>
<div class="form-group"><label>Описание</label><textarea name="description">{_escape(v.get('description',''))}</textarea></div>
<div class="form-group"><label>Точка начала</label><input name="start_point" value="{_escape(v.get('start_point',''))}"></div>
<div class="form-group"><label>Место получения приза</label><input name="prize_location" value="{_escape(v.get('prize_location',''))}"></div>
<div class="form-group"><label>Дата начала</label><input type="date" name="start_date" value="{_escape(v.get('start_date','') or '')}"></div>
<div class="form-group"><label>Дата окончания</label><input type="date" name="end_date" value="{_escape(v.get('end_date','') or '')}"></div>
<div class="form-group"><label>Попыток на вопрос (0=∞)</label><input type="number" name="max_attempts" value="{v.get('max_attempts',3)}" min="0"></div>
<button class="btn btn-primary">Сохранить</button>
</form>"""
    return layout(title, body, active="quests")


def quest_detail(quest, questions, attempts):
    qid = quest["id"]
    status_map = {
        "draft": '<span class="badge badge-yellow">Черновик</span>',
        "published": '<span class="badge badge-green">Опубликован</span>',
        "archived": '<span class="badge badge-red">Архив</span>',
    }
    st = status_map.get(quest["status"], quest["status"])

    action_btns = ""
    if quest["status"] == "draft":
        action_btns = f'<form method="POST" action="/admin/quests/{qid}/publish" style="display:inline"><button class="btn btn-success">Опубликовать</button></form> '
    elif quest["status"] == "published":
        action_btns = f'<form method="POST" action="/admin/quests/{qid}/archive" style="display:inline"><button class="btn btn-secondary">В архив</button></form> '

    qrows = ""
    for q in questions:
        qrows += (
            f"<tr>"
            f"<td>{q['order_num']}</td>"
            f"<td>{_escape(q['task_text'][:80])}</td>"
            f"<td>{_escape(q['correct_answer'])}</td>"
            f"<td>"
            f"<a href='/admin/questions/{q['id']}/edit' class='btn btn-primary btn-sm'>✏️</a> "
            f"<form method='POST' action='/admin/questions/{q['id']}/delete' style='display:inline'>"
            f"<button class='btn btn-danger btn-sm' onclick='return confirm(\"Удалить?\")'>🗑️</button></form>"
            f"</td></tr>"
        )
    if not qrows:
        qrows = '<tr><td colspan="4" class="empty">Нет вопросов</td></tr>'

    arows = ""
    for a in attempts:
        gift = "✅" if a["gift_given"] else "❌"
        status = "Завершён" if a["status"] == "completed" else "В процессе"
        arows += (
            f"<tr>"
            f"<td>{_escape(a['max_user_id'])}</td>"
            f"<td>{_escape(a['phone'] or '—')}</td>"
            f"<td>{status}</td>"
            f"<td>{gift}</td>"
            f"<td>{_escape(a['started_at'] or '')}</td>"
            f"</tr>"
        )
    if not arows:
        arows = '<tr><td colspan="5" class="empty">Нет прохождений</td></tr>'

    body = f"""<h1>🗺️ {_escape(quest['name'])}</h1>
<a href="/admin/quests" class="back-link">← Назад к списку</a>

<div class="card">
<h3>Информация</h3>
<p><strong>Статус:</strong> {st}</p>
<p><strong>Описание:</strong> {_escape(quest['description'] or '—')}</p>
<p><strong>Точка начала:</strong> {_escape(quest['start_point'] or '—')}</p>
<p><strong>Приз:</strong> {_escape(quest['prize_location'] or '—')}</p>
<p><strong>Даты:</strong> {_escape(quest['start_date'] or '∞')} — {_escape(quest['end_date'] or '∞')}</p>
<p><strong>Попыток на вопрос:</strong> {quest['max_attempts']}</p>
</div>

<div class="actions">
<a href="/admin/quests/{qid}/edit" class="btn btn-primary">✏️ Редактировать</a>
{action_btns}
<form method="POST" action="/admin/quests/{qid}/delete" style="display:inline"
  onsubmit="return confirm('Удалить квест и все вопросы?')">
<button class="btn btn-danger">🗑️ Удалить</button></form>
</div>

<h2>❓ Вопросы ({len(questions)})</h2>
<a href="/admin/quests/{qid}/questions/new" class="btn btn-primary btn-sm">+ Добавить вопрос</a>
<form method="POST" action="/admin/quests/{qid}/questions/import" enctype="multipart/form-data"
  style="display:inline;margin-left:8px">
<input type="file" name="csv_file" accept=".csv" style="display:inline;font-size:13px">
<button class="btn btn-secondary btn-sm">📥 Импорт CSV</button>
</form>
<table style="margin-top:12px"><tr><th>№</th><th>Задание</th><th>Ответ</th><th></th></tr>
{qrows}</table>

<h2>👥 Прошедшие ({len(attempts)})</h2>
<table><tr><th>MAX ID</th><th>Телефон</th><th>Статус</th><th>Подарок</th><th>Дата</th></tr>
{arows}</table>"""

    return layout(quest["name"], body, active="quests")


def question_form(quest_id, question=None):
    is_edit = question is not None
    title = "Редактирование вопроса" if is_edit else "Новый вопрос"
    action = (
        f"/admin/questions/{question['id']}"
        if is_edit
        else f"/admin/quests/{quest_id}/questions"
    )
    v = question or {}
    body = f"""<h1>{title}</h1>
<a href="/admin/quests/{quest_id}" class="back-link">← Назад к квесту</a>
<form method="POST" action="{action}">
<div class="form-group"><label>Порядковый номер</label><input type="number" name="order_num" value="{v.get('order_num',1)}" min="1" required></div>
<div class="form-group"><label>Справка/контекст</label><textarea name="context">{_escape(v.get('context',''))}</textarea></div>
<div class="form-group"><label>Задание</label><textarea name="task_text" required>{_escape(v.get('task_text',''))}</textarea></div>
<div class="form-group"><label>Правильный ответ</label><input name="correct_answer" value="{_escape(v.get('correct_answer',''))}" required></div>
<div class="form-group"><label>Пояснение</label><textarea name="explanation">{_escape(v.get('explanation',''))}</textarea></div>
<div class="form-group"><label>Подсказка</label><textarea name="hint">{_escape(v.get('hint',''))}</textarea></div>
<div class="form-group"><label>Попыток (переопределение, пусто = из квеста)</label><input type="number" name="attempts_override" value="{v.get('attempts_override') or ''}" min="0"></div>
<button class="btn btn-primary">Сохранить</button>
</form>"""
    return layout(title, body, active="quests")


def stats_page(stats):
    body = f"""<h1>📈 Статистика</h1>
<div class="stats-grid">
<div class="stat-card"><div class="num">{stats['total_users']}</div><div class="label">Пользователей</div></div>
<div class="stat-card"><div class="num">{stats['total_quests']}</div><div class="label">Квестов всего</div></div>
<div class="stat-card"><div class="num">{stats['published_quests']}</div><div class="label">Опубликованных</div></div>
<div class="stat-card"><div class="num">{stats['completed_attempts']}</div><div class="label">Завершённых прохождений</div></div>
<div class="stat-card"><div class="num">{stats['active_attempts']}</div><div class="label">Активных прохождений</div></div>
<div class="stat-card"><div class="num">{stats['gifts_given']}</div><div class="label">Подарков выдано</div></div>
</div>"""
    return layout("Статистика", body, active="stats")
