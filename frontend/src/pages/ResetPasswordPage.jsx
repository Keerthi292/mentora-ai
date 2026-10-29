import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import BotAvatar from "../components/BotAvatar";
import useMe from "../hooks/useMe";

// The link from the "forgot password" email: /reset-password?token=...
// Choosing a new password logs in and opens the dashboard.
function ResetPasswordPage() {
  const [params] = useSearchParams();
  const token = params.get("token") ?? "";
  const { resetPassword } = useMe();
  const navigate = useNavigate();
  const [values, setValues] = useState({ password: "", confirm: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const change = (event) => setValues((current) => ({ ...current, [event.target.name]: event.target.value }));

  const submit = async (event) => {
    event.preventDefault();
    if (values.password !== values.confirm) {
      setError("The passwords don't match.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await resetPassword(token, values.password);
      navigate("/", { replace: true });
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
            <h1 className="h4 fw-bold mt-3 mb-1">Choose a new password</h1>
            <p className="text-body-secondary small mb-0">You'll be logged in, and logged out everywhere else.</p>
          </div>

          {!token ? (
            <div className="alert alert-danger py-2 small">
              This reset link is incomplete. Open the link from the email again, or{" "}
              <Link to="/forgot-password">ask for a new one</Link>.
            </div>
          ) : (
            <>
              {error && (
                <div className="alert alert-danger py-2 small">
                  {error}{" "}
                  {error.includes("expired") && <Link to="/forgot-password">Send a new link</Link>}
                </div>
              )}

              <form onSubmit={submit}>
                <div className="mb-3">
                  <label className="form-label" htmlFor="reset-password">
                    New password
                  </label>
                  <div className="input-group">
                    <input
                      id="reset-password"
                      name="password"
                      type={showPassword ? "text" : "password"}
                      className="form-control"
                      autoComplete="new-password"
                      minLength={8}
                      maxLength={128}
                      required
                      autoFocus
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
                  <div className="form-text">At least 8 characters.</div>
                </div>
                <div className="mb-3">
                  <label className="form-label" htmlFor="reset-confirm">
                    Repeat password
                  </label>
                  <input
                    id="reset-confirm"
                    name="confirm"
                    type={showPassword ? "text" : "password"}
                    className="form-control"
                    autoComplete="new-password"
                    required
                    value={values.confirm}
                    onChange={change}
                  />
                </div>
                <button type="submit" className="btn btn-gradient w-100 mt-2" disabled={busy}>
                  {busy ? <span className="spinner-border spinner-border-sm" role="status" /> : "Save and log in"}
                </button>
              </form>
            </>
          )}

          <p className="text-center small text-body-secondary mt-4 mb-0">
            <Link to="/login">Back to log in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default ResetPasswordPage;
