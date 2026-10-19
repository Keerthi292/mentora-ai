// Small wrapper around fetch() for calling the Mentora AI backend.
//
// Requests go to /api on this same site; Vite forwards them to the backend
// (BACKEND_URL in frontend/.env). So the login cookie (httpOnly, set by the
// backend) is sent automatically, and no token is ever handled in JavaScript.
const API_BASE_URL = "";

// Called when the backend says we're not logged in (401), e.g. the session expired
let onUnauthorized = () => {};
export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler;
}

/** Report a 401 from any request (fetch, upload, stream) so the app shows the login page. */
export function checkUnauthorized(status, path) {
  if (status === 401 && !path.startsWith("/api/auth/")) onUnauthorized();
}

/**
 * Call the backend and return the parsed JSON response.
 * Throws an Error (with the backend's message) when the request fails.
 *
 * Example: await apiRequest("/api/skills", { method: "POST", body: { name: "Python" } })
 */
export async function apiRequest(path, { method = "GET", body } = {}) {
  const options = { method, headers: {} };

  if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, options);
  } catch {
    // fetch only throws when the server can't be reached at all
    throw new Error("Cannot reach the backend. Is it running?");
  }

  // 204 No Content (e.g. after DELETE) has no body to parse
  const data = response.status === 204 ? null : await response.json().catch(() => null);

  if (!response.ok) {
    checkUnauthorized(response.status, path);
    const error = new Error(getErrorMessage(data, response.status));
    error.status = response.status;
    throw error;
  }
  return data;
}

// FastAPI errors look like {"detail": "..."} or, for validation (422),
// {"detail": [{"msg": "..."}, ...]}. Turn either into one readable string.
export function getErrorMessage(data, status) {
  const detail = data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join("; ");
  return `Request failed with status ${status}`;
}

// Shortcuts so pages can write api.get("/api/skills") etc.
export const api = {
  get: (path) => apiRequest(path),
  post: (path, body) => apiRequest(path, { method: "POST", body }),
  put: (path, body) => apiRequest(path, { method: "PUT", body }),
  patch: (path, body) => apiRequest(path, { method: "PATCH", body }),
  delete: (path) => apiRequest(path, { method: "DELETE" }),
};

export { API_BASE_URL };
