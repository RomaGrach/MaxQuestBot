const API_BASE = (import.meta.env.VITE_API_URL || "/api").replace(/\/$/, "");

class ApiError extends Error {
  constructor(message, status, payload) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  return response.text();
}

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});

  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  const payload = await parseResponse(response);

  if (!response.ok) {
    const message =
      payload?.error ||
      payload?.message ||
      (typeof payload === "string" && payload) ||
      `Request failed with status ${response.status}`;

    throw new ApiError(message, response.status, payload);
  }

  return payload;
}

function authHeaders(token) {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export { ApiError };

export function pingHealth() {
  return request("/health", {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
}

export function loginAdmin(payload) {
  return request("/admin/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getAdminStats(token) {
  return request("/admin/stats", {
    method: "GET",
    headers: authHeaders(token),
  });
}

export async function exportAdminStats(token) {
  const response = await fetch(`${API_BASE}/admin/stats/export.csv`, {
    method: "GET",
    headers: authHeaders(token),
  });

  if (!response.ok) {
    const payload = await parseResponse(response);
    throw new ApiError(payload?.error || "CSV export failed", response.status, payload);
  }

  return response.blob();
}

export function getAdminQuests(token) {
  return request("/admin/quests", {
    method: "GET",
    headers: authHeaders(token),
  });
}

export function createAdminQuest(token, payload) {
  return request("/admin/quests", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function updateAdminQuest(token, questId, payload) {
  return request(`/admin/quests/${questId}`, {
    method: "PUT",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function deleteAdminQuest(token, questId) {
  return request(`/admin/quests/${questId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
}

export function getAdminQuestions(token, questId) {
  return request(`/admin/quests/${questId}/questions`, {
    method: "GET",
    headers: authHeaders(token),
  });
}

export function createAdminQuestion(token, questId, payload) {
  return request(`/admin/quests/${questId}/questions`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function updateAdminQuestion(token, questId, questionId, payload) {
  return request(`/admin/quests/${questId}/questions/${questionId}`, {
    method: "PUT",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function deleteAdminQuestion(token, questId, questionId) {
  return request(`/admin/quests/${questId}/questions/${questionId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
}

export function getAdminUsers(token) {
  return request("/admin/users", {
    method: "GET",
    headers: authHeaders(token),
  });
}

export function getAdminUserAttempts(token, userId) {
  return request(`/admin/users/${userId}/attempts`, {
    method: "GET",
    headers: authHeaders(token),
  });
}

export function updateAdminUserComment(token, userId, payload) {
  return request(`/admin/users/${userId}/comment`, {
    method: "PATCH",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function markAdminGift(token, attemptId, payload) {
  return request(`/admin/attempts/${attemptId}/gift`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify(payload),
  });
}

export function registerBotUser(payload) {
  return request("/bot/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getBotQuests(maxUserId) {
  return request(`/bot/quests?max_user_id=${encodeURIComponent(maxUserId)}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
}

export function startBotQuest(questId, payload) {
  return request(`/bot/quests/${questId}/start`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getBotQuestState(questId, maxUserId) {
  return request(
    `/bot/quests/${questId}/state?max_user_id=${encodeURIComponent(maxUserId)}`,
    {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    },
  );
}

export function submitBotAnswer(questId, payload) {
  return request(`/bot/quests/${questId}/answer`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function requestBotHint(questId, payload) {
  return request(`/bot/quests/${questId}/hint`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
