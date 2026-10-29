import { useState } from "react";
import { Link } from "react-router-dom";

import BotAvatar from "../components/BotAvatar";
import { api } from "../services/api";

// "Forgot password?": ask for a reset link by email.
function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.post("/api/auth/forgot-password", { email: email.trim() });
      setSent(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-page d-flex align-items-center justify-content-center px-3 py-5">
      <div className="card auth-card shadow-lg w-100">
        <div className="card-body p-4 p-sm-5">
          <div className="text-center mb-4">
            <BotAvatar size={72} float sparkles={sent} />
            <h1 className="h4 fw-bold mt-3 mb-1">{sent ? "Check your email" : "Forgot your password?"}</h1>
            <p className="text-body-secondary small mb-0">
              {sent
                ? `If an account uses ${email.trim()}, we've sent it a link to choose a new password. Check your spam folder too.`
                : "Enter your email and we'll send you a link to choose a new one."}
            </p>
          </div>

          {error && <div className="alert alert-danger py-2 small">{error}</div>}

          {sent ? (
            <button type="button" className="btn btn-outline-secondary w-100" onClick={() => setSent(false)}>
              Use another email
            </button>
          ) : (
            <form onSubmit={submit}>
              <div className="mb-3">
                <label className="form-label" htmlFor="forgot-email">
                  Email
                </label>
                <input
                  id="forgot-email"
                  type="email"
                  className="form-control"
                  autoComplete="email"
                  maxLength={255}
                  required
                  autoFocus
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                />
              </div>
              <button type="submit" className="btn btn-gradient w-100 mt-2" disabled={busy}>
                {busy ? <span className="spinner-border spinner-border-sm" role="status" /> : "Send reset link"}
              </button>
            </form>
          )}

          <p className="text-center small text-body-secondary mt-4 mb-0">
            Remembered it? <Link to="/login">Log in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default ForgotPasswordPage;
