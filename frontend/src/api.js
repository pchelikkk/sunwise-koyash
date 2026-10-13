// KOYASH API client.
// Base URL comes from VITE_API_BASE_URL at build time.
// In Docker, nginx serves the SPA and reverse-proxies /api to backend.

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || "/api/v1").replace(
  /\/$/,
  "",
);

const TOKEN_KEY = "koyash_token";
const ANON_KEY = "koyash_anon_id";

let token = null;
try {
  token = localStorage.getItem(TOKEN_KEY);
} catch {
  token = null;
}

export function setToken(value) {
  token = value || null;
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* ignore storage errors */
  }
}

export function getToken() {
  return token;
}

export function logout() {
  setToken(null);
}

export function getAnonymousId() {
  let value = null;
  try {
    value = localStorage.getItem(ANON_KEY);
  } catch {
    value = null;
  }

  if (!value) {
    value =
      "anon-" +
      Math.random().toString(36).slice(2) +
      "-" +
      Date.now().toString(36);

    try {
      localStorage.setItem(ANON_KEY, value);
    } catch {
      /* ignore storage errors */
    }
  }

  return value;
}

export class ApiError extends Error {
  constructor(status, message, detail) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

function humanizeDetail(detail, status) {
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const loc = Array.isArray(item.loc) ? item.loc.join(".") : "field";
        return loc + ": " + (item.msg || "invalid value");
      })
      .join("; ");
  }

  if (typeof detail === "string" && detail) return detail;
  if (detail && typeof detail === "object" && detail.message) {
    const errors = Array.isArray(detail.errors)
      ? detail.errors
          .slice(0, 3)
          .map((item) => `строка ${item.row_number}: ${item.reason}`)
          .join("; ")
      : "";
    return errors ? `${detail.message} ${errors}` : detail.message;
  }

  if (status === 401) return "Нужно войти в аккаунт.";
  if (status === 403) return "Недостаточно прав.";
  if (status === 404) return "Запись не найдена.";
  if (status === 409) return "Такая запись уже существует.";
  if (status === 422) return "Проверьте заполнение полей.";

  return "Запрос не выполнен (" + status + ")";
}

async function request(path, options = {}) {
  const { method = "GET", body, auth = false } = options;
  const headers = {};
  let payload;

  if (body !== undefined) {
    const isFormData = typeof FormData !== "undefined" && body instanceof FormData;
    if (isFormData) {
      payload = body;
    } else {
      headers["Content-Type"] = "application/json";
      payload = JSON.stringify(body);
    }
  }

  if (auth) {
    if (!token) throw new ApiError(401, "Нужно войти в аккаунт.", null);
    headers["Authorization"] = "Bearer " + token;
  }

  let res;
  try {
    res = await fetch(BASE_URL + path, { method, headers, body: payload });
  } catch (networkError) {
    throw new ApiError(
      0,
      "Не удалось связаться с сервером. Проверьте соединение.",
      networkError,
    );
  }

  if (res.status === 204) return null;

  let data = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!res.ok) {
    const detail = data && typeof data === "object" ? data.detail : data;
    throw new ApiError(res.status, humanizeDetail(detail, res.status), detail);
  }

  return data;
}

export const getQuestionnaire = () => request("/questionnaire");

export const getRestrictionSuggestions = () =>
  request("/restrictions/suggestions");

export const createRecommendation = (payload) =>
  request("/recommendations", {
    method: "POST",
    body: { ...payload, anonymous_id: getAnonymousId() },
    auth: Boolean(getToken()),
  });

export const diagnoseSkin = (payload) =>
  request("/skin-diagnosis", { method: "POST", body: payload });

export function getProductCatalog(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    if (Array.isArray(value)) {
      value.filter(Boolean).forEach((item) => params.append(key, item));
      return;
    }
    params.set(key, String(value));
  });
  const query = params.toString();
  return request("/products/catalog" + (query ? "?" + query : ""));
}

export const getProduct = (externalId) =>
  request("/products/" + encodeURIComponent(externalId));

export const getRecommendation = (recommendationId) =>
  request(
    "/recommendations/" +
      encodeURIComponent(recommendationId) +
      "?anonymous_id=" +
      encodeURIComponent(getAnonymousId()),
    { auth: Boolean(getToken()) },
  );

export const submitFeedback = (recommendationId, payload) =>
  request(
    "/recommendations/" + encodeURIComponent(recommendationId) + "/feedback",
    {
      method: "POST",
      body: { ...payload, anonymous_id: getAnonymousId() },
      auth: Boolean(getToken()),
    },
  );

export const listReplacements = (recommendationId) =>
  request(
    "/recommendations/" +
      encodeURIComponent(recommendationId) +
      "/replacements?anonymous_id=" +
      encodeURIComponent(getAnonymousId()),
    { auth: Boolean(getToken()) },
  );

export const selectReplacement = (
  recommendationId,
  sessionId,
  productExternalId,
) =>
  request(
    "/recommendations/" +
      encodeURIComponent(recommendationId) +
      "/replacements/" +
      encodeURIComponent(sessionId) +
      "/select",
    {
      method: "POST",
      body: {
        product_external_id: productExternalId,
        anonymous_id: getAnonymousId(),
      },
      auth: Boolean(getToken()),
    },
  );

export const register = (payload) =>
  request("/auth/register", {
    method: "POST",
    body: { ...payload, anonymous_id: getAnonymousId() },
  });

export const login = (email, password) =>
  request("/auth/login", {
    method: "POST",
    body: {
      email: email.trim().toLowerCase(),
      password,
      anonymous_id: getAnonymousId(),
    },
  });

export const forgotPassword = (email) =>
  request("/auth/forgot-password", {
    method: "POST",
    body: { email: email.trim().toLowerCase() },
  });

export const resetPassword = (tokenValue, newPassword) =>
  request("/auth/reset-password", {
    method: "POST",
    body: { token: tokenValue, new_password: newPassword },
  });

export const getMe = () => request("/users/me", { auth: true });

export const updateMe = (payload) =>
  request("/users/me", { method: "PATCH", body: payload, auth: true });

export const getMyProfile = () => request("/users/me/profile", { auth: true });

export const updateMyProfile = (payload) =>
  request("/users/me/profile", {
    method: "PATCH",
    body: payload,
    auth: true,
  });

export const appendQuestionnaireHistory = (payload) =>
  request("/users/me/profile/questionnaire-history", {
    method: "POST",
    body: payload,
    auth: true,
  });

export const getMyRecommendations = (limit = 20, offset = 0) =>
  request(
    "/users/me/recommendations?limit=" +
      encodeURIComponent(limit) +
      "&offset=" +
      encodeURIComponent(offset),
    { auth: true },
  );

export const getFavorites = () =>
  request("/users/me/favorites", { auth: true });

export const addFavorite = (externalId) =>
  request("/users/me/favorites/" + encodeURIComponent(externalId), {
    method: "PUT",
    auth: true,
  });

export const removeFavorite = (externalId) =>
  request("/users/me/favorites/" + encodeURIComponent(externalId), {
    method: "DELETE",
    auth: true,
  });

export const getCosmeticBag = () =>
  request("/users/me/cosmetic-bag", { auth: true });

export const addCosmeticBagItem = (externalId) =>
  request("/users/me/cosmetic-bag/" + encodeURIComponent(externalId), {
    method: "PUT",
    auth: true,
  });

export const removeCosmeticBagItem = (externalId) =>
  request("/users/me/cosmetic-bag/" + encodeURIComponent(externalId), {
    method: "DELETE",
    auth: true,
  });

export const clearCosmeticBag = () =>
  request("/users/me/cosmetic-bag", {
    method: "DELETE",
    auth: true,
  });

export const getAdminDashboard = (days = 30) =>
  request("/admin/analytics/dashboard?days=" + encodeURIComponent(days), {
    auth: true,
  });

export const getAdminCatalogQuality = () =>
  request("/admin/catalog/quality", { auth: true });

export const getAdminCatalogIssues = (issue = "all", page = 1) =>
  request(
    "/admin/catalog/issues?issue=" +
      encodeURIComponent(issue) +
      "&page=" +
      encodeURIComponent(page) +
      "&page_size=25",
    { auth: true },
  );

export const updateAdminProduct = (externalId, payload) =>
  request("/admin/catalog/products/" + encodeURIComponent(externalId), {
    method: "PATCH",
    body: payload,
    auth: true,
  });

export const importAdminCatalogDataset = (file, synchronizeMissing = true) => {
  const body = new FormData();
  body.append("file", file);
  body.append("synchronize_missing", String(Boolean(synchronizeMissing)));
  return request("/admin/catalog/import", {
    method: "POST",
    body,
    auth: true,
  });
};

export const trackEvent = (eventType, payload = {}) =>
  request("/analytics/events", {
    method: "POST",
    body: {
      event_type: eventType,
      anonymous_id: getAnonymousId(),
      ...payload,
    },
    auth: Boolean(getToken()),
  }).catch(() => null);

export async function loadAuthState() {
  if (!getToken()) return null;

  try {
    const [user, profile] = await Promise.all([getMe(), getMyProfile()]);
    return { user, profile };
  } catch (error) {
    if (error && error.status === 401) setToken(null);
    throw error;
  }
}
