import { useEffect, useSyncExternalStore } from "react";

import { api, setUnauthorizedHandler } from "../services/api";

// Who is logged in, shared by the whole app (one /api/me request).
// status: "loading" | "in" (logged in) | "out" (show the login page) | "offline" (backend down)
let state = { status: "loading", me: null, error: "" };
const listeners = new Set();
let loading = null;

function setState(changes) {
  state = { ...state, ...changes };
  listeners.forEach((listener) => listener());
}

function subscribe(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

// Any request answered with 401 (e.g. the session expired) shows the login page
setUnauthorizedHandler(() => setState({ status: "out", me: null }));

function loadMe() {
  loading ??= api
    .get("/api/me")
    .then(
      (me) => setState({ status: "in", me, error: "" }),
      (err) => setState(err.status === 401 ? { status: "out", me: null } : { status: "offline", error: err.message })
    )
    .finally(() => {
      loading = null;
    });
  return loading;
}

const login = async (email, password) => {
  const me = await api.post("/api/auth/login", { email, password });
  setState({ status: "in", me });
};

const register = async (data) => {
  const me = await api.post("/api/auth/register", data);
  setState({ status: "in", me });
};

const resetPassword = async (email, code, password) => {
  const me = await api.post("/api/auth/reset-password", { email, code, password });
  setState({ status: "in", me });
};

const logout = async () => {
  await api.post("/api/auth/logout").catch(() => {}); // logged out here either way
  setState({ status: "out", me: null });
};

const update = async (changes) => {
  const me = await api.patch("/api/me", changes);
  setState({ me });
};

const retry = () => {
  setState({ status: "loading" });
  return loadMe();
};

/** First name to greet the user with, or "" if unknown. */
function firstName(me) {
  return me?.full_name?.trim().split(/\s+/)[0] ?? "";
}

/**
 * The logged-in user ({ id, full_name, email, theme }) and the login actions:
 * login(email, password), register({ full_name, email, password }),
 * resetPassword(email, code, password), logout(),
 * update({ full_name?, theme? }), retry() (after "offline").
 */
function useMe() {
  const current = useSyncExternalStore(subscribe, () => state);

  useEffect(() => {
    if (state.status === "loading") loadMe();
  }, []);

  return { ...current, name: firstName(current.me), login, register, resetPassword, logout, update, retry };
}

export default useMe;
