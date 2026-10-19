import { useState } from "react";
import { Link } from "react-router-dom";

import BotAvatar from "../components/BotAvatar";
import useMe from "../hooks/useMe";

// Log in (mode="login") or create an account (mode="register").
// Shown at any address while logged out; after logging in, that page opens.
function AuthPage({ mode }) {
  const isRegister = mode === "register";
  const { login, register } = useMe();
  const [values, setValues] = useState({ full_name: "", email: "", password: "", confirm: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const change = (event) => setValues((current) => ({ ...current, [event.target.name]: event.target.value }));

  const submit = async (event) => {
    event.preventDefault();
    if (isRegister && values.password !== values.confirm) {
      setError("The passwords don't match.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      if (isRegister) {
        await register({ full_name: values.full_name.trim(), email: values.email.trim(), password: values.password });
      } else {
        await login(values.email.trim(), values.password);
      }
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };

  return (
    <div className="auth-page d-flex align-items-center justify-content-center px-3 py-5">
      <div className="card auth-card shadow-lg w-100">
        <div className="card-body p-4 p-sm-5">
          <div className="text-center mb-4">
            <BotAvatar size={72} float sparkles />
            <h1 className="h4 fw-bold mt-3 mb-1">{isRegister ? "Create your account" : "Welcome back"}</h1>
            <p className="text-body-secondary small mb-0">
              {isRegister ? "Your own mentor, skills, goals and projects." : "Log in to continue with Mentora AI."}
            </p>
          </div>

          {error && <div className="alert alert-danger py-2 small">{error}</div>}

          <form onSubmit={submit}>
            {isRegister && (
              <div className="mb-3">
                <label className="form-label" htmlFor="auth-name">
                  Your name
                </label>
                <input
                  id="auth-name"
                  name="full_name"
                  className="form-control"
                  autoComplete="name"
                  maxLength={255}
                  required
                  value={values.full_name}
                  onChange={change}
                />
              </div>
            )}
            <div className="mb-3">
              <label className="form-label" htmlFor="auth-email">
                Email
              </label>
              <input
                id="auth-email"
                name="email"
                type="email"
                className="form-control"
                autoComplete="email"
                maxLength={255}
                required
                autoFocus={!isRegister}
                value={values.email}
                onChange={change}
              />
            </div>
            <div className="mb-3">
              <label className="form-label" htmlFor="auth-password">
                Password
              </label>
              <div className="input-group">
                <input
                  id="auth-password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  className="form-control"
                  autoComplete={isRegister ? "new-password" : "current-password"}
                  minLength={isRegister ? 8 : undefined}
                  maxLength={128}
                  required
                  value={values.password}
                  onChange={change}
                />
                <button
                  type="button"
                  className="btn btn-outline-secondary"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  title={showPassword ? "Hide password" : "Show password"}
                >
                  <i className={`bi ${showPassword ? "bi-eye-slash" : "bi-eye"}`} aria-hidden="true" />
                </button>
              </div>
              {isRegister && <div className="form-text">At least 8 characters.</div>}
            </div>
            {isRegister && (
              <div className="mb-3">
                <label className="form-label" htmlFor="auth-confirm">
                  Repeat password
                </label>
                <input
                  id="auth-confirm"
                  name="confirm"
                  type={showPassword ? "text" : "password"}
                  className="form-control"
                  autoComplete="new-password"
                  required
                  value={values.confirm}
                  onChange={change}
                />
              </div>
            )}

            <button type="submit" className="btn btn-gradient w-100 mt-2" disabled={busy}>
              {busy ? (
                <span className="spinner-border spinner-border-sm" role="status" />
              ) : isRegister ? (
                "Create account"
              ) : (
                "Log in"
              )}
            </button>
          </form>

          <p className="text-center small text-body-secondary mt-4 mb-0">
            {isRegister ? "Already have an account? " : "New to Mentora? "}
            <Link to={isRegister ? "/login" : "/register"}>{isRegister ? "Log in" : "Create an account"}</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default AuthPage;
