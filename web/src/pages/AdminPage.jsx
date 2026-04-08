import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ClipboardList,
  Compass,
  Database,
  DoorOpen,
  Flag,
  Gift,
  HelpCircle,
  LoaderCircle,
  Lock,
  MapPinned,
  PencilLine,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
  Trash2,
  UserRound,
  Users,
} from "lucide-react";
import {
  ApiError,
  createAdminQuestion,
  createAdminQuest,
  deleteAdminQuestion,
  deleteAdminQuest,
  exportAdminStats,
  getAdminQuestions,
  getAdminQuests,
  getAdminStats,
  getAdminUserAttempts,
  getAdminUsers,
  loginAdmin,
  markAdminGift,
  updateAdminQuestion,
  updateAdminQuest,
  updateAdminUserComment,
} from "../api";
import {
  ADMIN_SESSION_KEY,
  adminTabs,
  buildQuestionPayload,
  buildQuestPayload,
  buttonGhostClass,
  buttonPrimaryClass,
  buttonSecondaryClass,
  cx,
  defaultQuestForm,
  defaultQuestionForm,
  formatDateTime,
  getErrorMessage,
  inputClass,
  mapQuestionToForm,
  mapQuestToForm,
  panelClass,
  questStatusOptions,
  readStorage,
  removeStorage,
  semanticModeOptions,
  subtlePanelClass,
  writeStorage,
} from "../utils";
import { Button, EmptyState, Field, Notice, SectionHeader, StatusBadge } from "../ui";

const overviewCards = [
  { key: "users", label: "Пользователи", icon: Users },
  { key: "attempts", label: "Попытки", icon: Flag },
  { key: "completed", label: "Завершено", icon: ClipboardList },
  { key: "gift_issued", label: "Подарки выданы", icon: Gift },
];

function MessageIcon() {
  return <PencilLine className="h-4 w-4" />;
}

export default function AdminPage({ health }) {
  const [session, setSession] = useState(() => readStorage(ADMIN_SESSION_KEY, null));
  const [loginForm, setLoginForm] = useState({ username: "", password: "" });
  const [notice, setNotice] = useState(null);
  const [busyAction, setBusyAction] = useState("");
  const [section, setSection] = useState("overview");
  const [stats, setStats] = useState(null);
  const [quests, setQuests] = useState([]);
  const [users, setUsers] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [attempts, setAttempts] = useState([]);
  const [savedComments, setSavedComments] = useState({});
  const [giftDrafts, setGiftDrafts] = useState({});
  const [questFilter, setQuestFilter] = useState("");
  const [userFilter, setUserFilter] = useState("");
  const [selectedQuestId, setSelectedQuestId] = useState();
  const [selectedQuestionId, setSelectedQuestionId] = useState();
  const [selectedUserId, setSelectedUserId] = useState();
  const [questForm, setQuestForm] = useState(defaultQuestForm);
  const [questionForm, setQuestionForm] = useState(defaultQuestionForm);
  const [commentDraft, setCommentDraft] = useState("");

  const token = session?.token || "";
  const role = session?.role || "";

  const selectedQuest =
    selectedQuestId == null ? null : quests.find((item) => item.id === selectedQuestId) || null;
  const selectedQuestion =
    selectedQuestionId == null
      ? null
      : questions.find((item) => item.id === selectedQuestionId) || null;
  const selectedUser =
    selectedUserId == null ? null : users.find((item) => item.id === selectedUserId) || null;

  const visibleQuests = quests.filter((quest) =>
    `${quest.title} ${quest.description}`.toLowerCase().includes(questFilter.toLowerCase()),
  );
  const visibleUsers = users.filter((user) =>
    `${user.max_user_id} ${user.phone}`.toLowerCase().includes(userFilter.toLowerCase()),
  );

  async function bootstrap(currentToken) {
    const [statsResult, questsResult, usersResult] = await Promise.all([
      getAdminStats(currentToken),
      getAdminQuests(currentToken),
      getAdminUsers(currentToken),
    ]);
    setStats(statsResult);
    setQuests(questsResult.items || []);
    setUsers(usersResult.items || []);
  }

  async function loadQuestions(questId) {
    if (!questId) {
      setQuestions([]);
      return;
    }

    const result = await getAdminQuestions(token, questId);
    setQuestions(result.items || []);
  }

  async function loadAttempts(userId) {
    if (!userId) {
      setAttempts([]);
      return;
    }

    const result = await getAdminUserAttempts(token, userId);
    setAttempts(result.items || []);
  }

  function handleError(error) {
    if (error instanceof ApiError && error.status === 401) {
      removeStorage(ADMIN_SESSION_KEY);
      setSession(null);
    }

    setNotice({
      type: "error",
      title: "Запрос отклонён",
      message: getErrorMessage(error),
    });
  }

  useEffect(() => {
    if (!token) {
      return;
    }

    setBusyAction("bootstrap");
    bootstrap(token)
      .catch(handleError)
      .finally(() => setBusyAction(""));
  }, [token]);

  useEffect(() => {
    if (selectedQuestId === undefined && quests.length > 0) {
      setSelectedQuestId(quests[0].id);
    }
  }, [quests, selectedQuestId]);

  useEffect(() => {
    if (selectedUserId === undefined && users.length > 0) {
      setSelectedUserId(users[0].id);
    }
  }, [users, selectedUserId]);

  useEffect(() => {
    if (selectedQuestId === null) {
      setQuestForm(defaultQuestForm);
      setQuestions([]);
      setSelectedQuestionId(null);
      setQuestionForm(defaultQuestionForm);
      return;
    }

    if (!selectedQuest) {
      return;
    }

    setQuestForm(mapQuestToForm(selectedQuest));
    loadQuestions(selectedQuest.id).catch(handleError);
  }, [selectedQuest]);

  useEffect(() => {
    if (questions.length === 0) {
      setSelectedQuestionId(null);
      setQuestionForm(defaultQuestionForm);
      return;
    }

    if (selectedQuestionId === undefined) {
      setSelectedQuestionId(questions[0].id);
      return;
    }

    if (selectedQuestion) {
      setQuestionForm(mapQuestionToForm(selectedQuestion));
    }
  }, [questions, selectedQuestionId, selectedQuestion]);

  useEffect(() => {
    if (selectedUserId == null) {
      setAttempts([]);
      setCommentDraft("");
      return;
    }

    loadAttempts(selectedUserId).catch(handleError);
    setCommentDraft(savedComments[selectedUserId] || "");
  }, [selectedUserId]);

  async function handleLogin(event) {
    event.preventDefault();
    setBusyAction("login");
    setNotice(null);

    try {
      const result = await loginAdmin(loginForm);
      const nextSession = {
        token: result.token,
        username: result.username,
        role: result.role,
      };
      setSession(nextSession);
      writeStorage(ADMIN_SESSION_KEY, nextSession);
      setNotice({
        type: "success",
        title: "Сессия открыта",
        message: `Вход выполнен как ${result.username}.`,
      });
    } catch (error) {
      handleError(error);
    } finally {
      setBusyAction("");
    }
  }

  function handleLogout() {
    removeStorage(ADMIN_SESSION_KEY);
    setSession(null);
    setStats(null);
    setQuests([]);
    setUsers([]);
    setQuestions([]);
    setAttempts([]);
    setSelectedQuestId(undefined);
    setSelectedQuestionId(undefined);
    setSelectedUserId(undefined);
    setNotice({
      type: "info",
      title: "Сессия завершена",
      message: "Токен удалён из локального хранилища.",
    });
  }

  async function handleRefresh() {
    setBusyAction("refresh");
    try {
      await bootstrap(token);
      if (selectedQuestId) {
        await loadQuestions(selectedQuestId);
      }
      if (selectedUserId) {
        await loadAttempts(selectedUserId);
      }
      setNotice({
        type: "success",
        title: "Данные обновлены",
        message: "Админка синхронизирована с backend.",
      });
    } catch (error) {
      handleError(error);
    } finally {
      setBusyAction("");
    }
  }

  async function handleQuestSubmit(event) {
    event.preventDefault();
    setBusyAction("quest");
    setNotice(null);

    try {
      const payload = buildQuestPayload(selectedQuestId, questForm);
      const updated = selectedQuestId
        ? await updateAdminQuest(token, selectedQuestId, payload)
        : await createAdminQuest(token, payload);
      const nextQuests = await getAdminQuests(token);
      setQuests(nextQuests.items || []);
      setSelectedQuestId(updated.id);
      setNotice({
        type: "success",
        title: selectedQuestId ? "Квест обновлён" : "Квест создан",
        message: `Сохранён квест «${updated.title}».`,
      });
    } catch (error) {
      handleError(error);
    } finally {
      setBusyAction("");
    }
  }

  async function handleQuestDelete() {
    if (!selectedQuestId || !window.confirm("Удалить выбранный квест?")) {
      return;
    }

    setBusyAction("quest-delete");
    try {
      await deleteAdminQuest(token, selectedQuestId);
      const result = await getAdminQuests(token);
      setQuests(result.items || []);
      setSelectedQuestId(undefined);
      setNotice({
        type: "success",
        title: "Квест удалён",
        message: "Запись удалена из backend.",
      });
    } catch (error) {
      handleError(error);
    } finally {
      setBusyAction("");
    }
  }

  async function handleQuestionSubmit(event) {
    event.preventDefault();
    if (!selectedQuestId) {
      setNotice({
        type: "info",
        title: "Нужен квест",
        message: "Сначала выберите или создайте квест, затем добавляйте вопросы.",
      });
      return;
    }

    setBusyAction("question");
    setNotice(null);

    try {
      const payload = buildQuestionPayload(selectedQuestionId, selectedQuestId, questionForm);
      const saved = selectedQuestionId
        ? await updateAdminQuestion(token, selectedQuestId, selectedQuestionId, payload)
        : await createAdminQuestion(token, selectedQuestId, payload);
      await loadQuestions(selectedQuestId);
      setSelectedQuestionId(saved.id);
      setNotice({
        type: "success",
        title: selectedQuestionId ? "Вопрос обновлён" : "Вопрос создан",
        message: `Порядок: ${saved.order}.`,
      });
    } catch (error) {
      handleError(error);
    } finally {
      setBusyAction("");
    }
  }

  async function handleQuestionDelete() {
    if (!selectedQuestId || !selectedQuestionId || !window.confirm("Удалить выбранный вопрос?")) {
      return;
    }

    setBusyAction("question-delete");
    try {
      await deleteAdminQuestion(token, selectedQuestId, selectedQuestionId);
      await loadQuestions(selectedQuestId);
      setSelectedQuestionId(undefined);
      setNotice({
        type: "success",
        title: "Вопрос удалён",
        message: "Запись удалена из backend.",
      });
    } catch (error) {
      handleError(error);
    } finally {
      setBusyAction("");
    }
  }

  async function handleSaveComment(event) {
    event.preventDefault();
    if (!selectedUserId) {
      return;
    }

    setBusyAction("comment");
    try {
      const updated = await updateAdminUserComment(token, selectedUserId, {
        comment: commentDraft,
      });
      setSavedComments((current) => ({
        ...current,
        [selectedUserId]: updated.comment || "",
      }));
      setNotice({
        type: "success",
        title: "Комментарий сохранён",
        message:
          updated.comment?.trim() || "Поле очищено. Текущий API не возвращает комментарий в общем списке пользователей.",
      });
    } catch (error) {
      handleError(error);
    } finally {
      setBusyAction("");
    }
  }

  async function handleGiftMark(attemptId) {
    setBusyAction(`gift-${attemptId}`);
    try {
      await markAdminGift(token, attemptId, { comment: giftDrafts[attemptId] || "" });
      if (selectedUserId) {
        await loadAttempts(selectedUserId);
      }
      const nextStats = await getAdminStats(token);
      setStats(nextStats);
      setNotice({
        type: "success",
        title: "Выдача подарка отмечена",
        message: "Статус попытки обновлён.",
      });
    } catch (error) {
      handleError(error);
    } finally {
      setBusyAction("");
    }
  }

  async function handleExportCsv() {
    setBusyAction("csv");
    try {
      const blob = await exportAdminStats(token);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "maxquest-stats.csv";
      link.click();
      URL.revokeObjectURL(url);
      setNotice({
        type: "success",
        title: "CSV сформирован",
        message: "Файл выгружен через `/admin/stats/export.csv`.",
      });
    } catch (error) {
      handleError(error);
    } finally {
      setBusyAction("");
    }
  }

  if (!session) {
    return (
      <div className="mx-auto flex min-h-screen w-full max-w-6xl items-center px-4 py-6 sm:px-6 lg:px-8">
        <div className="grid w-full gap-6 lg:grid-cols-[0.9fr_1.1fr]">
          <section className={cx(panelClass, "grid gap-4 p-6")}>
            <div className="flex items-center gap-3 text-sm text-[color:var(--muted)]">
              <Lock className="h-4 w-4 text-[color:var(--accent)]" />
              <span>Вход в операторскую панель</span>
            </div>
            <div className="space-y-3">
              <h1 className="text-3xl font-semibold tracking-tight text-[color:var(--ink)]">Админка MaxQuestBot</h1>
              <p className="text-sm leading-6 text-[color:var(--muted)]">
                Интерфейс строится поверх готового Go-backend. После входа доступны статистика,
                пользователи, квесты, вопросы и отметка выдачи подарков.
              </p>
            </div>
            <div className={cx(subtlePanelClass, "grid gap-3 p-4 text-sm text-[color:var(--muted)]")}>
              <div className="flex items-center justify-between">
                <span>Health-check</span>
                <span className={health.state === "online" ? "text-emerald-700" : "text-rose-700"}>
                  {health.state === "online" ? "доступен" : "недоступен"}
                </span>
              </div>
              <div>
                <p className="text-[color:var(--ink)]">Локальные dev-учётки из `.env.example`</p>
                <p>`admin / admin123` и `operator / operator`</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-3">
              <Link className={buttonSecondaryClass} to="/">
                На главную
              </Link>
              <Link className={buttonSecondaryClass} to="/app">
                <Compass className="h-4 w-4" />
                <span>Открыть WebApp</span>
              </Link>
            </div>
          </section>

          <section className={cx(panelClass, "grid gap-4 p-6")}>
            <SectionHeader
              title="Авторизация"
              description="JWT-токен хранится локально и автоматически подставляется ко всем admin-запросам."
            />
            <div className="px-5 pb-5">
              <form className="grid gap-4" onSubmit={handleLogin}>
                <Field label="Логин">
                  <input className={inputClass} value={loginForm.username} onChange={(event) => setLoginForm((current) => ({ ...current, username: event.target.value }))} placeholder="admin" />
                </Field>
                <Field label="Пароль">
                  <input className={inputClass} type="password" value={loginForm.password} onChange={(event) => setLoginForm((current) => ({ ...current, password: event.target.value }))} placeholder="••••••••" />
                </Field>
                <Notice notice={notice} onClose={() => setNotice(null)} />
                <button className={buttonPrimaryClass} disabled={busyAction === "login"} type="submit">
                  {busyAction === "login" ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
                  <span>Войти</span>
                </button>
              </form>
            </div>
          </section>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen px-4 py-4 sm:px-6 lg:px-8">
      <div className="mx-auto grid min-h-[calc(100vh-2rem)] max-w-7xl gap-4 lg:grid-cols-[248px_1fr]">
        <aside className={cx(panelClass, "flex flex-col overflow-hidden")}>
          <div className="border-b border-[color:var(--line)] px-5 py-5">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[color:var(--muted)]">MaxQuestBot</p>
            <h1 className="mt-2 text-xl font-semibold text-[color:var(--ink)]">Операторская панель</h1>
            <p className="mt-2 text-sm text-[color:var(--muted)]">{session.username} • {role}</p>
          </div>
          <nav className="grid gap-1 px-3 py-4">
            {adminTabs.map(({ key, label }) => (
              <button
                key={key}
                className={cx(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm font-medium transition",
                  section === key
                    ? "bg-[color:var(--surface-2)] text-[color:var(--ink)]"
                    : "text-[color:var(--muted)] hover:bg-[color:var(--surface-2)] hover:text-[color:var(--ink)]",
                )}
                onClick={() => setSection(key)}
              >
                <span>{label}</span>
              </button>
            ))}
          </nav>
          <div className="mt-auto border-t border-[color:var(--line)] px-5 py-4 text-sm text-[color:var(--muted)]">
            <div className="flex items-center justify-between">
              <span>API</span>
              <span className={health.state === "online" ? "text-emerald-700" : "text-rose-700"}>
                {health.state === "online" ? "online" : "offline"}
              </span>
            </div>
            <div className="mt-4 flex gap-2">
              <Button className="flex-1" icon={RefreshCw} onClick={handleRefresh}>
                Обновить
              </Button>
              <button className={buttonGhostClass} onClick={handleLogout}>
                <DoorOpen className="h-4 w-4" />
                <span>Выйти</span>
              </button>
            </div>
          </div>
        </aside>

        <main className={cx(panelClass, "overflow-hidden")}>
          <SectionHeader
            title={
              section === "overview"
                ? "Обзор"
                : section === "quests"
                  ? "Квесты и вопросы"
                  : section === "users"
                    ? "Пользователи и попытки"
                    : "Связка с WebApp"
            }
            description={
              section === "overview"
                ? "Сводные метрики и текущее состояние backend-данных."
                : section === "quests"
                  ? role === "admin"
                    ? "CRUD квестов и вопросов через защищённые admin-эндпоинты."
                    : "Роль operator не имеет доступа к изменению квестов."
                  : section === "users"
                    ? "Список участников, история прохождений и отметка выдачи подарков."
                    : "Памятка по интеграции WebApp с MAX и Go-backend."
            }
            actions={
              <div className="flex flex-wrap gap-2">
                {section === "overview" ? (
                  <Button icon={Database} onClick={handleExportCsv}>
                    CSV
                  </Button>
                ) : null}
                <Link className={buttonSecondaryClass} to="/app">
                  <Compass className="h-4 w-4" />
                  <span>Открыть WebApp</span>
                </Link>
              </div>
            }
          />

          <div className="grid gap-4 p-5">
            <Notice notice={notice} onClose={() => setNotice(null)} />
            {section === "overview" ? (
              <OverviewSection
                quests={quests}
                selectedQuestId={selectedQuestId}
                selectedUserId={selectedUserId}
                setSection={setSection}
                setSelectedQuestId={setSelectedQuestId}
                setSelectedUserId={setSelectedUserId}
                stats={stats}
                users={users}
              />
            ) : null}
            {section === "quests" ? (
              role !== "admin" ? (
                <EmptyState
                  icon={Lock}
                  title="Недостаточно прав"
                  description="Роль operator не может создавать или редактировать квесты и вопросы."
                />
              ) : (
                <QuestsSection
                  busyAction={busyAction}
                  handleQuestDelete={handleQuestDelete}
                  handleQuestSubmit={handleQuestSubmit}
                  handleQuestionDelete={handleQuestionDelete}
                  handleQuestionSubmit={handleQuestionSubmit}
                  questFilter={questFilter}
                  questForm={questForm}
                  questionForm={questionForm}
                  questions={questions}
                  selectedQuestId={selectedQuestId}
                  selectedQuestionId={selectedQuestionId}
                  setQuestFilter={setQuestFilter}
                  setQuestForm={setQuestForm}
                  setQuestionForm={setQuestionForm}
                  setSelectedQuestId={setSelectedQuestId}
                  setSelectedQuestionId={setSelectedQuestionId}
                  visibleQuests={visibleQuests}
                />
              )
            ) : null}
            {section === "users" ? (
              <UsersSection
                attempts={attempts}
                busyAction={busyAction}
                commentDraft={commentDraft}
                giftDrafts={giftDrafts}
                handleGiftMark={handleGiftMark}
                handleSaveComment={handleSaveComment}
                selectedUser={selectedUser}
                selectedUserId={selectedUserId}
                setCommentDraft={setCommentDraft}
                setGiftDrafts={setGiftDrafts}
                setSelectedUserId={setSelectedUserId}
                setUserFilter={setUserFilter}
                userFilter={userFilter}
                visibleUsers={visibleUsers}
              />
            ) : null}
            {section === "webapp" ? <WebappSection /> : null}
          </div>
        </main>
      </div>
    </div>
  );
}

function OverviewSection({
  quests,
  selectedQuestId,
  selectedUserId,
  setSection,
  setSelectedQuestId,
  setSelectedUserId,
  stats,
  users,
}) {
  return (
    <section className="grid gap-4">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {overviewCards.map(({ key, label, icon: Icon }) => (
          <div key={key} className={cx(panelClass, "grid gap-2 p-4")}>
            <div className="flex items-center justify-between">
              <span className="text-sm text-[color:var(--muted)]">{label}</span>
              <Icon className="h-4 w-4 text-[color:var(--accent)]" />
            </div>
            <span className="text-3xl font-semibold tracking-tight text-[color:var(--ink)]">
              {stats?.[key] ?? "—"}
            </span>
          </div>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className={cx(panelClass, "overflow-hidden")}>
          <SectionHeader title="Квесты" description="Публикация и готовность контента к мероприятию." />
          <div className="grid gap-3 p-5">
            {quests.length ? (
              quests.map((quest) => (
                <button
                  key={quest.id}
                  className={cx(
                    "grid gap-2 rounded-lg border border-[color:var(--line)] px-4 py-3 text-left transition hover:border-[color:var(--accent)]",
                    selectedQuestId === quest.id && "border-[color:var(--accent)] bg-[color:var(--surface-2)]",
                  )}
                  onClick={() => {
                    setSection("quests");
                    setSelectedQuestId(quest.id);
                  }}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-semibold text-[color:var(--ink)]">{quest.title}</span>
                    <StatusBadge value={quest.status} />
                  </div>
                  <p className="text-sm text-[color:var(--muted)]">{quest.start_point || "Точка старта не задана"}</p>
                </button>
              ))
            ) : (
              <EmptyState
                icon={MapPinned}
                title="Квестов пока нет"
                description="После подключения PostgreSQL и создания первых записей список появится здесь."
              />
            )}
          </div>
        </div>

        <div className={cx(panelClass, "overflow-hidden")}>
          <SectionHeader title="Участники" description="Сводка по зарегистрированным пользователям." />
          <div className="grid gap-3 p-5">
            {users.length ? (
              users.slice(0, 6).map((user) => (
                <button
                  key={user.id}
                  className={cx(
                    "flex items-center justify-between rounded-lg border border-[color:var(--line)] px-4 py-3 text-left transition hover:border-[color:var(--accent)]",
                    selectedUserId === user.id && "border-[color:var(--accent)] bg-[color:var(--surface-2)]",
                  )}
                  onClick={() => {
                    setSection("users");
                    setSelectedUserId(user.id);
                  }}
                >
                  <div>
                    <p className="font-semibold text-[color:var(--ink)]">{user.max_user_id}</p>
                    <p className="text-sm text-[color:var(--muted)]">{user.phone || "Телефон не указан"}</p>
                  </div>
                  <div className="text-right text-sm text-[color:var(--muted)]">
                    <p className="font-semibold text-[color:var(--ink)]">{user.completed_quests}</p>
                    <p>завершено</p>
                  </div>
                </button>
              ))
            ) : (
              <EmptyState
                icon={Users}
                title="Пользователей пока нет"
                description="Когда участники зарегистрируются через WebApp или MAX, они появятся в этом разделе."
              />
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

function QuestsSection({
  busyAction,
  handleQuestDelete,
  handleQuestSubmit,
  handleQuestionDelete,
  handleQuestionSubmit,
  questFilter,
  questForm,
  questionForm,
  questions,
  selectedQuestId,
  selectedQuestionId,
  setQuestFilter,
  setQuestForm,
  setQuestionForm,
  setSelectedQuestId,
  setSelectedQuestionId,
  visibleQuests,
}) {
  return (
    <section className="grid gap-4 xl:grid-cols-[320px_1fr]">
      <div className={cx(panelClass, "overflow-hidden")}>
        <SectionHeader
          title="Список квестов"
          actions={
            <Button
              className="px-3"
              icon={Plus}
              onClick={() => {
                setSelectedQuestId(null);
                setSelectedQuestionId(null);
                setQuestForm(defaultQuestForm);
                setQuestionForm(defaultQuestionForm);
              }}
            >
              Новый
            </Button>
          }
        />
        <div className="grid gap-3 p-5">
          <label className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[color:var(--muted)]" />
            <input
              className={cx(inputClass, "pl-9")}
              placeholder="Фильтр по названию"
              value={questFilter}
              onChange={(event) => setQuestFilter(event.target.value)}
            />
          </label>
          {visibleQuests.length ? (
            visibleQuests.map((quest) => (
              <button
                key={quest.id}
                className={cx(
                  "grid gap-2 rounded-lg border border-[color:var(--line)] px-4 py-3 text-left transition hover:border-[color:var(--accent)]",
                  selectedQuestId === quest.id && "border-[color:var(--accent)] bg-[color:var(--surface-2)]",
                )}
                onClick={() => {
                  setSelectedQuestId(quest.id);
                  setSelectedQuestionId(undefined);
                }}
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="font-semibold text-[color:var(--ink)]">{quest.title}</span>
                  <StatusBadge value={quest.status} />
                </div>
                <p className="text-sm text-[color:var(--muted)]">{quest.description || "Без описания"}</p>
              </button>
            ))
          ) : (
            <EmptyState icon={MapPinned} title="Совпадений нет" description="Измените фильтр или создайте новый квест." />
          )}
        </div>
      </div>

      <div className="grid gap-4">
        <form className={cx(panelClass, "overflow-hidden")} onSubmit={handleQuestSubmit}>
          <SectionHeader
            title={selectedQuestId ? "Редактор квеста" : "Новый квест"}
            description="Форма совпадает с DTO `CreateQuestRequest` и `UpdateQuestRequest`."
            actions={
              <div className="flex flex-wrap gap-2">
                {selectedQuestId ? (
                  <Button className="text-rose-700 hover:border-rose-300 hover:text-rose-700" icon={Trash2} onClick={handleQuestDelete} type="button">
                    Удалить
                  </Button>
                ) : null}
                <button className={buttonPrimaryClass} disabled={busyAction === "quest"} type="submit">
                  {busyAction === "quest" ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <PencilLine className="h-4 w-4" />}
                  <span>Сохранить квест</span>
                </button>
              </div>
            }
          />
          <div className="grid gap-4 p-5 lg:grid-cols-2">
            <Field label="Название">
              <input className={inputClass} value={questForm.title} onChange={(event) => setQuestForm((current) => ({ ...current, title: event.target.value }))} />
            </Field>
            <Field label="Статус">
              <select className={inputClass} value={questForm.status} onChange={(event) => setQuestForm((current) => ({ ...current, status: event.target.value }))}>
                {questStatusOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Точка старта">
              <input className={inputClass} value={questForm.startPoint} onChange={(event) => setQuestForm((current) => ({ ...current, startPoint: event.target.value }))} />
            </Field>
            <Field label="Информация о призе">
              <input className={inputClass} value={questForm.prizeInfo} onChange={(event) => setQuestForm((current) => ({ ...current, prizeInfo: event.target.value }))} />
            </Field>
            <Field label="Старт доступности">
              <input className={inputClass} type="datetime-local" value={questForm.startAt} onChange={(event) => setQuestForm((current) => ({ ...current, startAt: event.target.value }))} />
            </Field>
            <Field label="Конец доступности">
              <input className={inputClass} type="datetime-local" value={questForm.endAt} onChange={(event) => setQuestForm((current) => ({ ...current, endAt: event.target.value }))} />
            </Field>
            <Field label="Максимум попыток по умолчанию">
              <input className={inputClass} min="0" type="number" value={questForm.defaultMaxAttempts} onChange={(event) => setQuestForm((current) => ({ ...current, defaultMaxAttempts: event.target.value }))} />
            </Field>
            <label className={cx(subtlePanelClass, "flex items-center justify-between px-4 py-3")}>
              <div>
                <p className="text-sm font-medium text-[color:var(--ink)]">Разрешить повтор до выдачи подарка</p>
                <p className="text-xs text-[color:var(--muted)]">Поле `allow_retry_before_gift`</p>
              </div>
              <input checked={questForm.allowRetryBeforeGift} className="h-4 w-4 accent-[color:var(--accent)]" type="checkbox" onChange={(event) => setQuestForm((current) => ({ ...current, allowRetryBeforeGift: event.target.checked }))} />
            </label>
            <Field label="Описание">
              <textarea className={cx(inputClass, "min-h-28 resize-y")} value={questForm.description} onChange={(event) => setQuestForm((current) => ({ ...current, description: event.target.value }))} />
            </Field>
          </div>
        </form>

        <QuestionsEditor
          busyAction={busyAction}
          handleQuestionDelete={handleQuestionDelete}
          handleQuestionSubmit={handleQuestionSubmit}
          questionForm={questionForm}
          questions={questions}
          selectedQuestId={selectedQuestId}
          selectedQuestionId={selectedQuestionId}
          setQuestionForm={setQuestionForm}
          setSelectedQuestionId={setSelectedQuestionId}
        />
      </div>
    </section>
  );
}

function QuestionsEditor({
  busyAction,
  handleQuestionDelete,
  handleQuestionSubmit,
  questionForm,
  questions,
  selectedQuestId,
  selectedQuestionId,
  setQuestionForm,
  setSelectedQuestionId,
}) {
  return (
    <div className={cx(panelClass, "overflow-hidden")}>
      <SectionHeader
        title="Вопросы выбранного квеста"
        description={selectedQuestId ? "Форма совпадает с DTO `CreateQuestionRequest` / `UpdateQuestionRequest`." : "Сначала сохраните квест, затем добавляйте вопросы."}
        actions={
          selectedQuestId ? (
            <Button
              icon={Plus}
              onClick={() => {
                setSelectedQuestionId(null);
                setQuestionForm(defaultQuestionForm);
              }}
            >
              Новый вопрос
            </Button>
          ) : null
        }
      />
      {!selectedQuestId ? (
        <div className="p-5">
          <EmptyState icon={HelpCircle} title="Квест ещё не выбран" description="После создания квеста здесь появится список вопросов и форма их редактирования." />
        </div>
      ) : (
        <div className="grid gap-4 p-5 xl:grid-cols-[300px_1fr]">
          <div className="grid gap-3">
            {questions.length ? (
              questions
                .slice()
                .sort((left, right) => left.order - right.order)
                .map((question) => (
                  <button
                    key={question.id}
                    className={cx(
                      "grid gap-1 rounded-lg border border-[color:var(--line)] px-4 py-3 text-left transition hover:border-[color:var(--accent)]",
                      selectedQuestionId === question.id && "border-[color:var(--accent)] bg-[color:var(--surface-2)]",
                    )}
                    onClick={() => setSelectedQuestionId(question.id)}
                  >
                    <span className="text-xs font-semibold uppercase tracking-[0.12em] text-[color:var(--muted)]">Вопрос {question.order}</span>
                    <span className="font-medium text-[color:var(--ink)]">{question.task}</span>
                  </button>
                ))
            ) : (
              <EmptyState icon={HelpCircle} title="Вопросов пока нет" description="Добавьте первый вопрос для выбранного квеста." />
            )}
          </div>

          <form className="grid gap-4" onSubmit={handleQuestionSubmit}>
            <div className="grid gap-4 md:grid-cols-2">
              <Field label="Порядок">
                <input className={inputClass} min="1" type="number" value={questionForm.order} onChange={(event) => setQuestionForm((current) => ({ ...current, order: event.target.value }))} />
              </Field>
              <Field label="Режим проверки">
                <select className={inputClass} value={questionForm.semanticMode} onChange={(event) => setQuestionForm((current) => ({ ...current, semanticMode: event.target.value }))}>
                  {semanticModeOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Порог семантики">
                <input className={inputClass} max="1" min="0" step="0.01" type="number" value={questionForm.semanticThreshold} onChange={(event) => setQuestionForm((current) => ({ ...current, semanticThreshold: event.target.value }))} />
              </Field>
              <Field label="Лимит попыток для вопроса" hint="Оставьте пустым, чтобы применялось значение квеста.">
                <input className={inputClass} min="0" type="number" value={questionForm.maxAttempts} onChange={(event) => setQuestionForm((current) => ({ ...current, maxAttempts: event.target.value }))} />
              </Field>
              <Field label="Контекст">
                <textarea className={cx(inputClass, "min-h-24 resize-y")} value={questionForm.context} onChange={(event) => setQuestionForm((current) => ({ ...current, context: event.target.value }))} />
              </Field>
              <Field label="Задание">
                <textarea className={cx(inputClass, "min-h-24 resize-y")} value={questionForm.task} onChange={(event) => setQuestionForm((current) => ({ ...current, task: event.target.value }))} />
              </Field>
              <Field label="Правильный ответ">
                <textarea className={cx(inputClass, "min-h-20 resize-y")} value={questionForm.correctAnswer} onChange={(event) => setQuestionForm((current) => ({ ...current, correctAnswer: event.target.value }))} />
              </Field>
              <Field label="Подсказка">
                <textarea className={cx(inputClass, "min-h-20 resize-y")} value={questionForm.hint} onChange={(event) => setQuestionForm((current) => ({ ...current, hint: event.target.value }))} />
              </Field>
              <Field label="Пояснение">
                <textarea className={cx(inputClass, "min-h-24 resize-y")} value={questionForm.explanation} onChange={(event) => setQuestionForm((current) => ({ ...current, explanation: event.target.value }))} />
              </Field>
            </div>

            <div className="flex flex-wrap justify-end gap-2">
              {selectedQuestionId ? (
                <Button className="text-rose-700 hover:border-rose-300 hover:text-rose-700" icon={Trash2} onClick={handleQuestionDelete} type="button">
                  Удалить
                </Button>
              ) : null}
              <button className={buttonPrimaryClass} disabled={busyAction === "question"} type="submit">
                {busyAction === "question" ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <PencilLine className="h-4 w-4" />}
                <span>Сохранить вопрос</span>
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

function UsersSection({
  attempts,
  busyAction,
  commentDraft,
  giftDrafts,
  handleGiftMark,
  handleSaveComment,
  selectedUser,
  selectedUserId,
  setCommentDraft,
  setGiftDrafts,
  setSelectedUserId,
  setUserFilter,
  userFilter,
  visibleUsers,
}) {
  return (
    <section className="grid gap-4 xl:grid-cols-[320px_1fr]">
      <div className={cx(panelClass, "overflow-hidden")}>
        <SectionHeader title="Участники" description="Поиск по `max_user_id` и телефону." />
        <div className="grid gap-3 p-5">
          <label className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[color:var(--muted)]" />
            <input className={cx(inputClass, "pl-9")} placeholder="Поиск пользователя" value={userFilter} onChange={(event) => setUserFilter(event.target.value)} />
          </label>
          {visibleUsers.length ? (
            visibleUsers.map((user) => (
              <button
                key={user.id}
                className={cx(
                  "flex items-center justify-between rounded-lg border border-[color:var(--line)] px-4 py-3 text-left transition hover:border-[color:var(--accent)]",
                  selectedUserId === user.id && "border-[color:var(--accent)] bg-[color:var(--surface-2)]",
                )}
                onClick={() => setSelectedUserId(user.id)}
              >
                <div>
                  <p className="font-semibold text-[color:var(--ink)]">{user.max_user_id}</p>
                  <p className="text-sm text-[color:var(--muted)]">{user.phone || "Телефон не указан"}</p>
                </div>
                <div className="text-right text-xs text-[color:var(--muted)]">
                  <p className="text-lg font-semibold text-[color:var(--ink)]">{user.completed_quests}</p>
                  <p>квестов</p>
                </div>
              </button>
            ))
          ) : (
            <EmptyState icon={Users} title="Совпадений нет" description="Измените поисковую строку или дождитесь регистрации участников." />
          )}
        </div>
      </div>

      <div className={cx(panelClass, "overflow-hidden")}>
        <SectionHeader
          title={selectedUser ? `Пользователь ${selectedUser.max_user_id}` : "Карточка пользователя"}
          description={selectedUser ? "Комментарий сохраняется через `/admin/users/{user_id}/comment`." : "Выберите пользователя слева."}
        />
        {selectedUser ? (
          <div className="grid gap-4 p-5 md:grid-cols-[0.8fr_1.2fr]">
            <div className={cx(subtlePanelClass, "grid gap-3 p-4 text-sm")}>
              <div className="flex items-center gap-3 text-[color:var(--ink)]">
                <UserRound className="h-4 w-4 text-[color:var(--accent)]" />
                <p className="font-semibold">{selectedUser.max_user_id}</p>
              </div>
              <p className="text-[color:var(--muted)]">{selectedUser.phone || "Телефон не указан"}</p>
              <p className="text-[color:var(--muted)]">Завершено квестов: {selectedUser.completed_quests}</p>
              <form className="grid gap-3" onSubmit={handleSaveComment}>
                <Field label="Комментарий оператора" hint="Текущий backend не отдаёт комментарий в общем списке, поэтому UI показывает последнюю сохранённую версию.">
                  <textarea className={cx(inputClass, "min-h-28 resize-y")} value={commentDraft} onChange={(event) => setCommentDraft(event.target.value)} />
                </Field>
                <button className={buttonPrimaryClass} disabled={busyAction === "comment"} type="submit">
                  {busyAction === "comment" ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <MessageIcon />}
                  <span>Сохранить комментарий</span>
                </button>
              </form>
            </div>

            <div className="grid gap-3">
              {attempts.length ? (
                attempts.map((attempt) => (
                  <div key={attempt.attempt_id} className={cx(panelClass, "grid gap-4 p-4")}>
                    <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center gap-3">
                          <h3 className="text-base font-semibold text-[color:var(--ink)]">{attempt.quest_title || `Квест #${attempt.quest_id}`}</h3>
                          <StatusBadge value={attempt.status} />
                        </div>
                        <p className="text-sm text-[color:var(--muted)]">
                          Старт: {formatDateTime(attempt.started_at)}
                          {attempt.completed_at ? ` • Финиш: ${formatDateTime(attempt.completed_at)}` : ""}
                        </p>
                        {attempt.gift_comment ? <p className="text-sm text-[color:var(--muted)]">Комментарий по подарку: {attempt.gift_comment}</p> : null}
                      </div>
                      <div className="text-sm">
                        {attempt.gift_issued ? (
                          <p className="font-semibold text-emerald-700">Подарок выдан {formatDateTime(attempt.gift_issued_at)}</p>
                        ) : (
                          <p className="font-semibold text-amber-700">Подарок ещё не отмечен</p>
                        )}
                      </div>
                    </div>

                    {!attempt.gift_issued && attempt.status === "completed" ? (
                      <div className="grid gap-3 rounded-lg border border-[color:var(--line)] bg-[color:var(--surface-2)] p-4">
                        <Field label="Комментарий к выдаче">
                          <input className={inputClass} placeholder="Подарок выдан на стойке №1" value={giftDrafts[attempt.attempt_id] || ""} onChange={(event) => setGiftDrafts((current) => ({ ...current, [attempt.attempt_id]: event.target.value }))} />
                        </Field>
                        <button className={buttonPrimaryClass} disabled={busyAction === `gift-${attempt.attempt_id}`} onClick={() => handleGiftMark(attempt.attempt_id)} type="button">
                          {busyAction === `gift-${attempt.attempt_id}` ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Gift className="h-4 w-4" />}
                          <span>Отметить выдачу</span>
                        </button>
                      </div>
                    ) : null}
                  </div>
                ))
              ) : (
                <EmptyState icon={Flag} title="Попыток пока нет" description="После старта квестов здесь появится история прохождений пользователя." />
              )}
            </div>
          </div>
        ) : (
          <div className="p-5">
            <EmptyState icon={Users} title="Пользователь не выбран" description="Выберите участника из списка слева, чтобы посмотреть попытки и сохранить комментарий." />
          </div>
        )}
      </div>
    </section>
  );
}

function WebappSection() {
  return (
    <section className="grid gap-4 lg:grid-cols-2">
      <div className={cx(panelClass, "grid gap-4 p-5")}>
        <div className="flex items-center gap-3">
          <Compass className="h-5 w-5 text-[color:var(--accent)]" />
          <h2 className="text-lg font-semibold text-[color:var(--ink)]">Что уже заведено</h2>
        </div>
        <ul className="grid gap-2 text-sm text-[color:var(--ink)]">
          <li>Регистрация пользователя через `POST /bot/register`.</li>
          <li>Выбор только опубликованных квестов через `GET /bot/quests`.</li>
          <li>Старт, состояние, ответ и подсказка для активного прохождения.</li>
          <li>Локальное хранение `max_user_id`, телефона и текущего квеста.</li>
        </ul>
        <Link className={buttonPrimaryClass} to="/app">
          <Compass className="h-4 w-4" />
          <span>Перейти в WebApp</span>
        </Link>
      </div>

      <div className={cx(panelClass, "grid gap-4 p-5")}>
        <div className="flex items-center gap-3">
          <Database className="h-5 w-5 text-[color:var(--accent)]" />
          <h2 className="text-lg font-semibold text-[color:var(--ink)]">Что учесть при запуске</h2>
        </div>
        <ul className="grid gap-2 text-sm text-[color:var(--ink)]">
          <li>Backend сейчас без подключённой PostgreSQL, поэтому часть действий может падать ещё до UI.</li>
          <li>Во время разработки фронт ожидает backend на `http://localhost:8080` через Vite-прокси.</li>
          <li>Для production лучше держать фронт и backend за одним доменом или reverse-proxy по `/api`.</li>
          <li>Источник истины по формату запросов — `back/maxbot.postman_collection.json` и Go-хендлеры.</li>
        </ul>
      </div>
    </section>
  );
}
