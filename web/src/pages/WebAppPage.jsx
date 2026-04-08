import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Compass,
  Flag,
  HelpCircle,
  LoaderCircle,
  RefreshCw,
  ShieldCheck,
  Trash2,
  UserRound,
} from "lucide-react";
import {
  BOT_ACTIVE_QUEST_KEY,
  BOT_SESSION_KEY,
  buildBotFeedback,
  buttonPrimaryClass,
  buttonSecondaryClass,
  cx,
  defaultBotSession,
  getErrorMessage,
  inputClass,
  panelClass,
  readStorage,
  removeStorage,
  writeStorage,
} from "../utils";
import {
  getBotQuestState,
  getBotQuests,
  registerBotUser,
  requestBotHint,
  startBotQuest,
  submitBotAnswer,
} from "../api";
import { Button, EmptyState, Field, Notice, SectionHeader, StatusBadge } from "../ui";

export default function WebAppPage({ health }) {
  const [session, setSession] = useState(() => readStorage(BOT_SESSION_KEY, defaultBotSession));
  const [quests, setQuests] = useState([]);
  const [selectedQuestId, setSelectedQuestId] = useState(() =>
    readStorage(BOT_ACTIVE_QUEST_KEY, null),
  );
  const [questState, setQuestState] = useState(null);
  const [registeredUser, setRegisteredUser] = useState(null);
  const [feedback, setFeedback] = useState(null);
  const [answerDraft, setAnswerDraft] = useState("");
  const [busyAction, setBusyAction] = useState("");
  const [notice, setNotice] = useState(null);

  const selectedQuest =
    selectedQuestId == null ? null : quests.find((item) => item.id === Number(selectedQuestId)) || null;

  async function loadQuests(maxUserId) {
    if (!maxUserId) {
      setQuests([]);
      return;
    }

    const result = await getBotQuests(maxUserId);
    setQuests(result.items || []);
  }

  async function syncQuestState(questId, silent = false) {
    if (!questId || !session.maxUserId) {
      return;
    }

    try {
      const result = await getBotQuestState(questId, session.maxUserId);
      setQuestState({
        ...result,
        quest: quests.find((item) => item.id === questId) || selectedQuest,
      });
      if (!silent) {
        setNotice({
          type: "success",
          title: "Состояние обновлено",
          message: "UI повторно синхронизирован с backend.",
        });
      }
    } catch (error) {
      setNotice({
        type: "error",
        title: "Не удалось получить состояние",
        message: getErrorMessage(error),
      });
    }
  }

  useEffect(() => {
    if (!session.maxUserId) {
      return;
    }

    loadQuests(session.maxUserId).catch((error) => {
      setNotice({
        type: "error",
        title: "Список квестов недоступен",
        message: getErrorMessage(error),
      });
    });
  }, [session.maxUserId]);

  useEffect(() => {
    if (!selectedQuestId || !session.maxUserId) {
      return;
    }

    syncQuestState(Number(selectedQuestId), true);
  }, []);

  function persistSession(nextSession) {
    setSession(nextSession);
    writeStorage(BOT_SESSION_KEY, nextSession);
  }

  function clearActiveQuest() {
    setSelectedQuestId(null);
    setQuestState(null);
    setAnswerDraft("");
    setFeedback(null);
    removeStorage(BOT_ACTIVE_QUEST_KEY);
  }

  async function handleRegister(event) {
    event.preventDefault();
    setBusyAction("register");
    setNotice(null);

    try {
      const payload = {
        max_user_id: session.maxUserId.trim(),
        phone: session.phone,
        consent: session.consent,
      };
      const result = await registerBotUser(payload);
      setRegisteredUser(result);
      persistSession({
        maxUserId: payload.max_user_id,
        phone: payload.phone,
        consent: payload.consent,
      });
      await loadQuests(payload.max_user_id);
      setNotice({
        type: "success",
        title: "Участник зарегистрирован",
        message: "Можно выбирать опубликованный квест и начинать прохождение.",
      });
    } catch (error) {
      setNotice({
        type: "error",
        title: "Регистрация не выполнена",
        message: getErrorMessage(error),
      });
    } finally {
      setBusyAction("");
    }
  }

  async function handleStartQuest(questId) {
    setBusyAction(`start-${questId}`);
    setNotice(null);

    try {
      const result = await startBotQuest(questId, {
        max_user_id: session.maxUserId,
      });

      setSelectedQuestId(questId);
      writeStorage(BOT_ACTIVE_QUEST_KEY, questId);
      setQuestState({
        quest: result.quest,
        attempt: result.attempt,
        current_question: result.current_question,
        completed: false,
        prize_info: result.quest.prize_info,
      });
      setFeedback({
        tone: "success",
        title: "Квест запущен",
        body: "Первый вопрос готов к ответу.",
        extra: "",
      });
    } catch (error) {
      setNotice({
        type: "error",
        title: "Не удалось запустить квест",
        message: getErrorMessage(error),
      });
    } finally {
      setBusyAction("");
    }
  }

  async function handleAnswer(event) {
    event.preventDefault();
    if (!selectedQuestId) {
      return;
    }

    setBusyAction("answer");
    setNotice(null);

    try {
      const result = await submitBotAnswer(selectedQuestId, {
        max_user_id: session.maxUserId,
        answer: answerDraft,
      });

      setFeedback(buildBotFeedback(result));
      setQuestState((current) => ({
        ...current,
        attempt: current?.attempt
          ? {
              ...current.attempt,
              id: result.attempt_id,
              status: result.status,
              current_question_order:
                result.next_question?.order || current.attempt.current_question_order,
            }
          : { id: result.attempt_id, status: result.status },
        current_question: result.next_question || current?.current_question || null,
        completed: Boolean(result.completed),
        prize_info: result.prize_info || current?.prize_info || current?.quest?.prize_info || "",
      }));

      if (result.completed) {
        removeStorage(BOT_ACTIVE_QUEST_KEY);
      } else if (result.next_question) {
        setAnswerDraft("");
      }
    } catch (error) {
      setNotice({
        type: "error",
        title: "Ответ не отправлен",
        message: getErrorMessage(error),
      });
    } finally {
      setBusyAction("");
    }
  }

  async function handleHint() {
    if (!selectedQuestId) {
      return;
    }

    setBusyAction("hint");
    setNotice(null);

    try {
      const result = await requestBotHint(selectedQuestId, {
        max_user_id: session.maxUserId,
      });
      setFeedback({
        tone: "muted",
        title: `Подсказка к вопросу ${result.question_order}`,
        body: result.hint,
        extra: "",
      });
    } catch (error) {
      setNotice({
        type: "error",
        title: "Подсказка недоступна",
        message: getErrorMessage(error),
      });
    } finally {
      setBusyAction("");
    }
  }

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 py-6 sm:px-6 lg:px-8">
      <header className={cx(panelClass, "grid gap-6 px-6 py-6 lg:grid-cols-[1fr_auto] lg:items-end")}>
        <div className="space-y-3">
          <div className="flex items-center gap-3 text-sm text-[color:var(--muted)]">
            <Compass className="h-4 w-4 text-[color:var(--accent)]" />
            <span>WebApp участника</span>
            <span className="text-[color:var(--line-strong)]">/</span>
            <span>поток для MAX</span>
          </div>
          <h1 className="text-3xl font-semibold tracking-tight text-[color:var(--ink)] sm:text-4xl">
            Регистрация, выбор квеста и ответы на вопросы в одном экране.
          </h1>
          <p className="max-w-3xl text-sm leading-6 text-[color:var(--muted)] sm:text-base">
            Этот интерфейс опирается только на публичные `/bot`-эндпоинты backend. Если база
            пока не подключена, UI останется рабочим и покажет точный текст ошибки от сервиса.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link className={buttonSecondaryClass} to="/">
            <ArrowRight className="h-4 w-4" />
            <span>На главную</span>
          </Link>
          <Link className={buttonSecondaryClass} to="/admin">
            <ShieldCheck className="h-4 w-4" />
            <span>В админку</span>
          </Link>
        </div>
      </header>

      <div className="mt-6 grid gap-6 xl:grid-cols-[360px_1fr]">
        <aside className="grid gap-4">
          <section className={cx(panelClass, "overflow-hidden")}>
            <SectionHeader
              title="Профиль участника"
              description="Требуется `max_user_id` и согласие на обработку данных."
            />
            <form className="grid gap-4 p-5" onSubmit={handleRegister}>
              <Field label="MAX user id">
                <input
                  className={inputClass}
                  value={session.maxUserId}
                  onChange={(event) =>
                    persistSession({
                      ...session,
                      maxUserId: event.target.value,
                    })
                  }
                  placeholder="900001"
                />
              </Field>
              <Field label="Телефон">
                <input
                  className={inputClass}
                  value={session.phone}
                  onChange={(event) =>
                    persistSession({
                      ...session,
                      phone: event.target.value,
                    })
                  }
                  placeholder="+7 900 000-00-00"
                />
              </Field>
              <label className={cx(panelClass, "flex items-start gap-3 px-4 py-3 text-sm text-[color:var(--ink)]")}>
                <input
                  checked={session.consent}
                  className="mt-0.5 h-4 w-4 accent-[color:var(--accent)]"
                  type="checkbox"
                  onChange={(event) =>
                    persistSession({
                      ...session,
                      consent: event.target.checked,
                    })
                  }
                />
                <span>Подтверждаю согласие на обработку персональных данных.</span>
              </label>
              <button className={buttonPrimaryClass} disabled={busyAction === "register"} type="submit">
                {busyAction === "register" ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <UserRound className="h-4 w-4" />}
                <span>Сохранить и зарегистрировать</span>
              </button>
              {registeredUser ? (
                <div className={cx(panelClass, "grid gap-2 p-4 text-sm")}>
                  <p className="font-semibold text-[color:var(--ink)]">Пользователь зарегистрирован</p>
                  <p className="text-[color:var(--muted)]">
                    ID: {registeredUser.max_user_id} • телефон: {registeredUser.phone || "не указан"}
                  </p>
                </div>
              ) : null}
            </form>
          </section>

          <section className={cx(panelClass, "overflow-hidden")}>
            <SectionHeader
              title="Опубликованные квесты"
              description="Список приходит из `GET /bot/quests`."
            />
            <div className="grid gap-3 p-5">
              {!session.maxUserId ? (
                <EmptyState
                  icon={UserRound}
                  title="Сначала укажите `max_user_id`"
                  description="Без регистрации backend не отдаст список опубликованных квестов."
                />
              ) : quests.length ? (
                quests.map((quest) => (
                  <div key={quest.id} className={cx(panelClass, "grid gap-3 p-4")}>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h3 className="font-semibold text-[color:var(--ink)]">{quest.title}</h3>
                        <p className="mt-1 text-sm text-[color:var(--muted)]">{quest.description || "Описание не заполнено"}</p>
                      </div>
                      <StatusBadge value={quest.status} />
                    </div>
                    <div className="grid gap-1 text-sm text-[color:var(--muted)]">
                      <p>Старт: {quest.start_point || "не указан"}</p>
                      <p>Попыток по умолчанию: {quest.default_max_attempts || "без лимита"}</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <button
                        className={buttonPrimaryClass}
                        disabled={busyAction === `start-${quest.id}`}
                        onClick={() => handleStartQuest(quest.id)}
                        type="button"
                      >
                        {busyAction === `start-${quest.id}` ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Flag className="h-4 w-4" />}
                        <span>{selectedQuestId === quest.id ? "Продолжить" : "Старт"}</span>
                      </button>
                      <Button
                        icon={RefreshCw}
                        disabled={busyAction === "sync" || selectedQuestId !== quest.id}
                        onClick={() => {
                          setBusyAction("sync");
                          syncQuestState(quest.id).finally(() => setBusyAction(""));
                        }}
                        type="button"
                      >
                        Состояние
                      </Button>
                    </div>
                  </div>
                ))
              ) : (
                <EmptyState
                  icon={Compass}
                  title="Квесты не получены"
                  description="Если backend или база ещё не запущены, здесь появится сообщение об ошибке выше."
                />
              )}
            </div>
          </section>
        </aside>

        <main className="grid gap-4">
          <Notice notice={notice} onClose={() => setNotice(null)} />
          <section className={cx(panelClass, "overflow-hidden")}>
            <SectionHeader
              title={selectedQuest ? `Активный квест: ${selectedQuest.title}` : "Прохождение"}
              description={
                questState?.completed
                  ? "Квест завершён, ниже сохранена информация для получения приза."
                  : "После запуска backend вернёт текущий вопрос и статус попытки."
              }
              actions={
                selectedQuestId ? (
                  <div className="flex flex-wrap gap-2">
                    <Button
                      icon={RefreshCw}
                      onClick={() => {
                        setBusyAction("sync");
                        syncQuestState(Number(selectedQuestId)).finally(() => setBusyAction(""));
                      }}
                    >
                      Обновить
                    </Button>
                    <Button icon={Trash2} onClick={clearActiveQuest}>
                      Сбросить
                    </Button>
                  </div>
                ) : null
              }
            />
            <div className="grid gap-4 p-5">
              {!selectedQuestId ? (
                <EmptyState
                  icon={Flag}
                  title="Квест ещё не запущен"
                  description="Зарегистрируйтесь и нажмите «Старт» у нужного опубликованного квеста."
                />
              ) : (
                <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
                  <div className={cx(panelClass, "grid gap-4 p-5")}>
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[color:var(--muted)]">
                          Текущее состояние
                        </p>
                        <p className="mt-1 text-base font-semibold text-[color:var(--ink)]">
                          {questState?.completed ? "Квест завершён" : "Открытый вопрос"}
                        </p>
                      </div>
                      <StatusBadge value={questState?.attempt?.status || "in_progress"} />
                    </div>

                    {questState?.current_question ? (
                      <div className="grid gap-4">
                        <div className={cx(panelClass, "grid gap-3 p-4")}>
                          <div>
                            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[color:var(--muted)]">
                              Контекст
                            </p>
                            <p className="mt-1 text-sm leading-6 text-[color:var(--ink)]">
                              {questState.current_question.context || "Контекст не задан."}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[color:var(--muted)]">
                              Задание
                            </p>
                            <p className="mt-1 text-base font-medium leading-7 text-[color:var(--ink)]">
                              {questState.current_question.task}
                            </p>
                          </div>
                        </div>

                        <form className="grid gap-4" onSubmit={handleAnswer}>
                          <Field label="Ваш ответ">
                            <textarea
                              className={cx(inputClass, "min-h-28 resize-y")}
                              value={answerDraft}
                              onChange={(event) => setAnswerDraft(event.target.value)}
                              placeholder="Введите ответ так, как его отправил бы пользователь в MAX"
                            />
                          </Field>
                          <div className="flex flex-wrap gap-2">
                            <button className={buttonPrimaryClass} disabled={busyAction === "answer"} type="submit">
                              {busyAction === "answer" ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
                              <span>Отправить ответ</span>
                            </button>
                            <Button icon={HelpCircle} onClick={handleHint} disabled={busyAction === "hint"} type="button">
                              {busyAction === "hint" ? "Запрашиваем..." : "Подсказка"}
                            </Button>
                          </div>
                        </form>
                      </div>
                    ) : questState?.completed ? (
                      <div className={cx(panelClass, "grid gap-3 p-4")}>
                        <p className="text-lg font-semibold text-[color:var(--ink)]">Квест завершён успешно</p>
                        <p className="text-sm leading-6 text-[color:var(--muted)]">
                          {questState.prize_info || "Информация о призе не заполнена."}
                        </p>
                      </div>
                    ) : (
                      <EmptyState
                        icon={RefreshCw}
                        title="Состояние ещё не подгружено"
                        description="Нажмите «Обновить», чтобы получить текущее состояние попытки с backend."
                      />
                    )}
                  </div>

                  <div className={cx(panelClass, "grid gap-4 p-5")}>
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-[color:var(--muted)]">
                        Сервис
                      </p>
                      <p className="mt-1 text-base font-semibold text-[color:var(--ink)]">
                        {health.state === "online" ? "Backend доступен" : "Backend недоступен"}
                      </p>
                    </div>
                    <div className="grid gap-2 text-sm text-[color:var(--muted)]">
                      <p>Пользователь: {session.maxUserId || "не задан"}</p>
                      <p>Телефон: {session.phone || "не указан"}</p>
                      <p>Текущий квест: {selectedQuest?.title || `#${selectedQuestId}`}</p>
                    </div>

                    {feedback ? (
                      <div
                        className={cx(
                          "grid gap-2 rounded-lg border p-4 text-sm",
                          feedback.tone === "success"
                            ? "border-emerald-200 bg-emerald-50"
                            : feedback.tone === "warning"
                              ? "border-amber-200 bg-amber-50"
                              : "border-stone-200 bg-stone-50",
                        )}
                      >
                        <p className="font-semibold text-[color:var(--ink)]">{feedback.title}</p>
                        <p className="text-[color:var(--muted)]">{feedback.body}</p>
                        {feedback.extra ? <p className="text-[color:var(--ink)]">{feedback.extra}</p> : null}
                      </div>
                    ) : (
                      <EmptyState
                        icon={AlertTriangle}
                        title="Пока без ответов"
                        description="После отправки ответа или запроса подсказки здесь появится реакция backend."
                      />
                    )}
                  </div>
                </div>
              )}
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
