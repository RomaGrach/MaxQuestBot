import { ArrowRight, CheckCircle2, Compass, Database, ShieldCheck, Users } from "lucide-react";
import { Link } from "react-router-dom";
import { buttonPrimaryClass, buttonSecondaryClass, cx, panelClass, subtlePanelClass } from "../utils";

export default function LandingPage({ health }) {
  return (
    <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 py-6 sm:px-6 lg:px-8">
      <header className={cx(panelClass, "grid gap-8 px-6 py-6 lg:grid-cols-[1.3fr_0.7fr]")}>
        <div className="space-y-5">
          <div className="flex items-center gap-3 text-sm text-[color:var(--muted)]">
            <ShieldCheck className="h-4 w-4 text-[color:var(--accent)]" />
            <span>MaxQuestBot</span>
            <span className="text-[color:var(--line-strong)]">/</span>
            <span>единый фронт для backend-ветки</span>
          </div>
          <div className="space-y-3">
            <h1 className="max-w-3xl text-3xl font-semibold tracking-tight text-[color:var(--ink)] sm:text-4xl">
              Спокойный рабочий интерфейс для операторов квеста и WebApp-экран для участников.
            </h1>
            <p className="max-w-2xl text-sm leading-6 text-[color:var(--muted)] sm:text-base">
              Приложение собрано под реальные эндпоинты из `back/maxbot.postman_collection.json`:
              логин администратора, CRUD квестов и вопросов, список пользователей,
              попытки, выдача подарков, регистрация участника и прохождение квеста через MAX.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link className={buttonPrimaryClass} to="/admin">
              <ShieldCheck className="h-4 w-4" />
              <span>Открыть админку</span>
            </Link>
            <Link className={buttonSecondaryClass} to="/app">
              <Compass className="h-4 w-4" />
              <span>Открыть WebApp</span>
            </Link>
          </div>
        </div>
        <div className={cx(subtlePanelClass, "grid gap-4 p-5")}>
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[color:var(--muted)]">
              Состояние интеграции
            </p>
            <p className="text-sm text-[color:var(--ink)]">
              Фронт ожидает backend по `/api`, а в dev-режиме Vite проксирует запросы в Go-сервис.
            </p>
          </div>
          <div className="grid gap-2 text-sm">
            <div className="flex items-center justify-between rounded-lg border border-[color:var(--line)] bg-[color:var(--surface)] px-3 py-2">
              <span className="text-[color:var(--muted)]">Health-check</span>
              <span
                className={cx(
                  "font-semibold",
                  health.state === "online"
                    ? "text-emerald-700"
                    : health.state === "offline"
                      ? "text-rose-700"
                      : "text-stone-600",
                )}
              >
                {health.state === "online"
                  ? "backend доступен"
                  : health.state === "offline"
                    ? "backend недоступен"
                    : "проверка..."}
              </span>
            </div>
            <div className="rounded-lg border border-[color:var(--line)] bg-[color:var(--surface)] px-3 py-2 text-[color:var(--muted)]">
              По `back/.env.example` локальные dev-учётки: `admin / admin123`, `operator / operator`.
            </div>
          </div>
        </div>
      </header>

      <main className="mt-6 grid gap-6 lg:grid-cols-2">
        <article className={cx(panelClass, "grid gap-4 p-6")}>
          <div className="flex items-center gap-3">
            <ShieldCheck className="h-5 w-5 text-[color:var(--accent)]" />
            <h2 className="text-lg font-semibold text-[color:var(--ink)]">Админка операторов</h2>
          </div>
          <p className="text-sm leading-6 text-[color:var(--muted)]">
            Создание и публикация квестов, управление вопросами, список пользователей,
            статистика, просмотр попыток и отметка выдачи подарков. Роль `operator`
            получает только блоки пользователей и статистики, а роль `admin` — полный доступ.
          </p>
          <ul className="grid gap-2 text-sm text-[color:var(--ink)]">
            <li className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-700" />
              JWT-логин по `/admin/auth/login`
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-700" />
              CRUD квестов и вопросов
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-700" />
              Статистика, экспорт CSV, попытки и выдача подарков
            </li>
          </ul>
        </article>

        <article className={cx(panelClass, "grid gap-4 p-6")}>
          <div className="flex items-center gap-3">
            <Compass className="h-5 w-5 text-[color:var(--accent)]" />
            <h2 className="text-lg font-semibold text-[color:var(--ink)]">WebApp участника</h2>
          </div>
          <p className="text-sm leading-6 text-[color:var(--muted)]">
            Регистрация по `max_user_id`, список доступных квестов, старт, текущий вопрос,
            ответ, подсказка и финальный экран с информацией по получению приза.
          </p>
          <ul className="grid gap-2 text-sm text-[color:var(--ink)]">
            <li className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-700" />
              Контракты из `/bot/register`, `/bot/quests`, `/start`, `/state`, `/answer`, `/hint`
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-700" />
              Сохранение локальной сессии и активного квеста между перезагрузками
            </li>
            <li className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-700" />
              Понятные состояния для отсутствующего backend или неготовой БД
            </li>
          </ul>
        </article>
      </main>

      <footer className="mt-6 flex flex-wrap items-center justify-between gap-3 text-sm text-[color:var(--muted)]">
        <div className="flex items-center gap-2">
          <Database className="h-4 w-4" />
          <span>Источник контрактов: Go-handlers и Postman-коллекция из `back/`.</span>
        </div>
        <div className="flex items-center gap-2">
          <Users className="h-4 w-4" />
          <span>Интерфейс ориентирован на сотрудников мероприятия и участников офлайн-квеста.</span>
        </div>
        <Link className="inline-flex items-center gap-2 font-medium text-[color:var(--ink)]" to="/admin">
          <span>Перейти к работе</span>
          <ArrowRight className="h-4 w-4" />
        </Link>
      </footer>
    </div>
  );
}
