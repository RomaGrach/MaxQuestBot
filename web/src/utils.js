export const ADMIN_SESSION_KEY = "maxquest.admin.session";
export const BOT_SESSION_KEY = "maxquest.bot.session";
export const BOT_ACTIVE_QUEST_KEY = "maxquest.bot.activeQuest";

export const questStatusOptions = [
  { value: "draft", label: "Черновик" },
  { value: "published", label: "Опубликован" },
  { value: "archived", label: "Архив" },
];

export const semanticModeOptions = [
  { value: "exact", label: "Точное сравнение" },
  { value: "semantic", label: "Сравнение по смыслу" },
];

export const adminTabs = [
  { key: "overview", label: "Обзор" },
  { key: "quests", label: "Квесты" },
  { key: "users", label: "Пользователи" },
  { key: "webapp", label: "WebApp" },
];

export const defaultQuestForm = {
  title: "",
  description: "",
  status: "draft",
  startPoint: "",
  prizeInfo: "",
  startAt: "",
  endAt: "",
  defaultMaxAttempts: 3,
  allowRetryBeforeGift: false,
};

export const defaultQuestionForm = {
  order: 1,
  context: "",
  task: "",
  correctAnswer: "",
  explanation: "",
  hint: "",
  semanticMode: "exact",
  semanticThreshold: 0.8,
  maxAttempts: "",
};

export const defaultBotSession = {
  maxUserId: "",
  phone: "",
  consent: true,
};

export const panelClass =
  "rounded-xl border border-[color:var(--line)] bg-[color:var(--surface)]";
export const subtlePanelClass =
  "rounded-xl border border-dashed border-[color:var(--line)] bg-[color:var(--surface-2)]";
export const inputClass =
  "w-full rounded-lg border border-[color:var(--line)] bg-[color:var(--surface)] px-3 py-2.5 text-sm text-[color:var(--ink)] outline-none transition focus:border-[color:var(--accent)] focus:ring-2 focus:ring-[color:var(--accent-soft)]";
export const buttonPrimaryClass =
  "inline-flex items-center justify-center gap-2 rounded-lg bg-[color:var(--accent)] px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-[color:var(--accent-strong)] disabled:cursor-not-allowed disabled:opacity-60";
export const buttonSecondaryClass =
  "inline-flex items-center justify-center gap-2 rounded-lg border border-[color:var(--line)] bg-[color:var(--surface)] px-4 py-2.5 text-sm font-medium text-[color:var(--ink)] transition hover:border-[color:var(--accent)] hover:text-[color:var(--accent-strong)] disabled:cursor-not-allowed disabled:opacity-60";
export const buttonGhostClass =
  "inline-flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-[color:var(--muted)] transition hover:bg-[color:var(--surface-2)] hover:text-[color:var(--ink)] disabled:cursor-not-allowed disabled:opacity-60";

export function cx(...parts) {
  return parts.filter(Boolean).join(" ");
}

export function readStorage(key, fallback) {
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

export function writeStorage(key, value) {
  window.localStorage.setItem(key, JSON.stringify(value));
}

export function removeStorage(key) {
  window.localStorage.removeItem(key);
}

export function formatDateTime(value) {
  if (!value) {
    return "—";
  }

  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function formatDateInput(value) {
  if (!value) {
    return "";
  }

  const date = new Date(value);
  const pad = (number) => String(number).padStart(2, "0");

  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(
    date.getHours(),
  )}:${pad(date.getMinutes())}`;
}

export function toApiDate(value) {
  return value ? new Date(value).toISOString() : null;
}

export function getErrorMessage(error) {
  if (error instanceof Error) {
    return error.message;
  }

  return "Не удалось выполнить запрос.";
}

export function mapQuestToForm(quest) {
  return {
    title: quest.title || "",
    description: quest.description || "",
    status: quest.status || "draft",
    startPoint: quest.start_point || "",
    prizeInfo: quest.prize_info || "",
    startAt: formatDateInput(quest.start_at),
    endAt: formatDateInput(quest.end_at),
    defaultMaxAttempts: quest.default_max_attempts || 0,
    allowRetryBeforeGift: Boolean(quest.allow_retry_before_gift),
  };
}

export function mapQuestionToForm(question) {
  return {
    order: question.order || 1,
    context: question.context || "",
    task: question.task || "",
    correctAnswer: question.correct_answer || "",
    explanation: question.explanation || "",
    hint: question.hint || "",
    semanticMode: question.semantic_mode || "exact",
    semanticThreshold: question.semantic_threshold ?? 0.8,
    maxAttempts: question.max_attempts ?? "",
  };
}

export function buildQuestPayload(questId, form) {
  return {
    id: questId || 0,
    title: form.title.trim(),
    description: form.description.trim(),
    status: form.status,
    start_point: form.startPoint.trim(),
    prize_info: form.prizeInfo.trim(),
    start_at: toApiDate(form.startAt),
    end_at: toApiDate(form.endAt),
    default_max_attempts: Number(form.defaultMaxAttempts) || 0,
    allow_retry_before_gift: Boolean(form.allowRetryBeforeGift),
  };
}

export function buildQuestionPayload(questionId, questId, form) {
  return {
    id: questionId || 0,
    quest_id: questId,
    order: Number(form.order) || 1,
    context: form.context.trim(),
    task: form.task.trim(),
    correct_answer: form.correctAnswer.trim(),
    explanation: form.explanation.trim(),
    hint: form.hint.trim(),
    semantic_mode: form.semanticMode,
    semantic_threshold: Number(form.semanticThreshold) || 0,
    max_attempts: form.maxAttempts === "" ? null : Number(form.maxAttempts),
  };
}

export function buildBotFeedback(result) {
  if (result.correct) {
    return {
      tone: "success",
      title: result.accepted_by_meaning
        ? "Ответ принят по смыслу"
        : "Ответ засчитан",
      body:
        result.completed
          ? "Квест завершён, ниже доступна информация по призу."
          : "Можно переходить к следующему вопросу.",
      extra: [result.correct_answer, result.explanation].filter(Boolean).join(" "),
    };
  }

  if (result.showed_correct_answer) {
    return {
      tone: "warning",
      title: "Лимит попыток исчерпан",
      body: "Система показала правильный ответ и автоматически сдвинула квест дальше.",
      extra: [result.correct_answer, result.explanation].filter(Boolean).join(" "),
    };
  }

  return {
    tone: "muted",
    title: "Ответ пока не принят",
    body:
      result.attempts_left != null
        ? `Осталось попыток: ${result.attempts_left}.`
        : "Можно попробовать ещё раз или запросить подсказку.",
    extra: result.hint || "",
  };
}
