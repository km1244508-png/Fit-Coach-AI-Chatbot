// Thin fetch wrapper. Auth is an HttpOnly cookie, so JS never touches the token.
const BASE = (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(message, { status = 0, code = "error", data = null, fieldErrors = {} } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.data = data;
    this.fieldErrors = fieldErrors;
  }
}

let unauthorizedHandler = null;
export const setUnauthorizedHandler = (fn) => {
  unauthorizedHandler = fn;
};

async function request(path, { method = "GET", body, signal, authEndpoint = false } = {}) {
  let res;
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      credentials: "include",
      headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal,
    });
  } catch (err) {
    if (err?.name === "AbortError") throw err;
    throw new ApiError("Can't reach the server. Check your connection and try again.", { status: 0, code: "network_error" });
  }

  if (res.status === 204) return null;
  let data = null;
  try {
    data = await res.json();
  } catch {
    /* non-JSON body */
  }

  if (!res.ok) {
    if (res.status === 401 && !authEndpoint && unauthorizedHandler) unauthorizedHandler();
    const fieldErrors = {};
    for (const e of data?.errors || []) if (e.field && !fieldErrors[e.field]) fieldErrors[e.field] = e.message;
    const message = typeof data?.detail === "string" ? data.detail : `Request failed (${res.status}). Please try again.`;
    throw new ApiError(message, { status: res.status, code: data?.code || "error", data, fieldErrors });
  }
  return data;
}

export const api = {
  register: (payload) => request("/auth/register", { method: "POST", body: payload, authEndpoint: true }),
  login: (payload) => request("/auth/login", { method: "POST", body: payload, authEndpoint: true }),
  logout: () => request("/auth/logout", { method: "POST", authEndpoint: true }),
  me: () => request("/auth/me", { authEndpoint: true }),

  listConversations: ({ limit = 100, skip = 0 } = {}) => request(`/conversations?limit=${limit}&skip=${skip}`),
  createConversation: () => request("/conversations", { method: "POST", body: {} }),
  getConversation: (id, { before, limit = 100, signal } = {}) =>
    request(`/conversations/${id}?limit=${limit}${before ? `&before=${before}` : ""}`, { signal }),
  renameConversation: (id, title) => request(`/conversations/${id}`, { method: "PATCH", body: { title } }),
  deleteConversation: (id) => request(`/conversations/${id}`, { method: "DELETE" }),
  sendMessage: (id, body) => request(`/conversations/${id}/messages`, { method: "POST", body }),
};
