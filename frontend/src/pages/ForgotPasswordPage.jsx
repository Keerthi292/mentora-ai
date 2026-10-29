import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import BotAvatar from "../components/BotAvatar";
import useMe from "../hooks/useMe";
import { api } from "../services/api";

const CODE_LENGTH = 6;
// Wait this long before "Send a new code" can be pressed again
const RESEND_SECONDS = 30;

// "Forgot password?": step 1 emails a 6-digit code, step 2 takes the code and a new
// password. Saving logs in, and the app then opens the dashboard.
function ForgotPasswordPage() {
  const { resetPassword } = useMe();
  const [step, setStep] = useState("email"); // "email" | "code"
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [values, setValues] = useState({ password: "", confirm: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [resendIn, setResendIn] = useState(0);

  useEffect(() => {
    if (resendIn <= 0) return;
    const timer = setTimeout(() => setResendIn((s) => s - 1), 1000);
    return () => clearTimeout(timer);
  }, [resendIn]);

  const sendCode = async () => {
    setBusy(true);
    setError("");
    try {
      await api.post("/api/auth/forgot-password", { email: email.trim() });
      setStep("code");
      setCode("");
      setResendIn(RESEND_SECONDS);
      return true;
    } catch (err) {
      setError(err.message);
      return false;
    } finally {
      setBusy(false);
    }
  };

  const submitEmail = (event) => {
    event.preventDefault();
    sendCode();
  };

  const resend = async () => {
    setNotice("");
    if (await sendCode()) setNotice("A new code is on its way. The old one no longer works.");
  };

  const submitReset = async (event) => {
    event.preventDefault();
    if (!/^\d{6}$/.test(code)) {
      setError(`Enter all ${CODE_LENGTH} digits of the code.`);
      return;
    }
    if (values.password !== values.confirm) {
      setError("The passwords don't match.");
      return;
    }
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await resetPassword(email.trim(), code, values.password);
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };

  const change = (event) => setValues((current) => ({ ...current, [event.target.name]: event.target.value }));

  return (
    <div className="auth-page d-flex align-items-center justify-content-center px-3 py-5">
      <div className="card auth-card shadow-lg w-100">
        <div className="card-body p-4 p-sm-5">
          <div className="text-center mb-4">
            <BotAvatar size={72} float sparkles={step === "code"} />
            <h1 className="h4 fw-bold mt-3 mb-1">{step === "code" ? "Check your email" : "Forgot your password?"}</h1>
            <p className="text-body-secondary small mb-0">
              {step === "code" ? (
                <>
                  If an account uses <strong className="text-body">{email.trim()}</strong>, we've sent it a{" "}
                  {CODE_LENGTH}-digit code. Check your spam folder too.
                </>
              ) : (
                "Enter your email and we'll send you a code to choose a new password."
              )}
            </p>
          </div>

          {error && <div className="alert alert-danger py-2 small">{error}</div>}
          {notice && !error && <div className="alert alert-success py-2 small">{notice}</div>}

          {step === "email" ? (
            <form onSubmit={submitEmail}>
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
                {busy ? <span className="spinner-border spinner-border-sm" role="status" /> : "Send code"}
              </button>
            </form>
          ) : (
            <form onSubmit={submitReset}>
              <div className="mb-3">
                <label className="form-label" htmlFor="reset-code-0">
                  Code
                </label>
                <CodeInput value={code} onChange={setCode} />
              </div>
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

              <div className="d-flex justify-content-between small mt-3">
                <button
                  type="button"
                  className="btn btn-link btn-sm p-0"
                  onClick={() => {
                    setStep("email");
                    setError("");
                    setNotice("");
                  }}
                >
                  Use another email
                </button>
                <button type="button" className="btn btn-link btn-sm p-0" onClick={resend} disabled={busy || resendIn > 0}>
                  {resendIn > 0 ? `Send a new code (${resendIn}s)` : "Send a new code"}
                </button>
              </div>
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

// One box per digit: typing moves to the next box, Backspace to the previous one,
// and pasting the whole code fills every box. The value is always 6 characters,
// with a space for each empty box, so clearing one box doesn't shift the others.
function CodeInput({ value, onChange }) {
  const boxes = useRef([]);
  const digits = Array.from({ length: CODE_LENGTH }, (_, i) => (value[i] ?? " ").trim());

  useEffect(() => {
    boxes.current[0]?.focus();
  }, []);

  const save = (next) => onChange(next.map((d) => d || " ").join(""));

  const fill = (start, typed) => {
    const clean = typed.replace(/\D/g, "").slice(0, CODE_LENGTH - start);
    if (!clean) return;
    const next = [...digits];
    clean.split("").forEach((d, i) => (next[start + i] = d));
    save(next);
    boxes.current[Math.min(start + clean.length, CODE_LENGTH - 1)]?.focus();
  };

  const keyDown = (index, event) => {
    if (event.key === "Backspace") {
      event.preventDefault();
      // Clear this box, or if it's already empty, the one before
      const target = digits[index] ? index : Math.max(index - 1, 0);
      const next = [...digits];
      next[target] = "";
      save(next);
      boxes.current[target]?.focus();
    } else if (event.key === "ArrowLeft") {
      boxes.current[index - 1]?.focus();
    } else if (event.key === "ArrowRight") {
      boxes.current[index + 1]?.focus();
    }
  };

  return (
    <div className="code-input">
      {digits.map((digit, i) => (
        <input
          key={i}
          id={`reset-code-${i}`}
          ref={(el) => (boxes.current[i] = el)}
          className={`form-control code-box ${digit ? "filled" : ""}`}
          inputMode="numeric"
          // Phones offer the code from the email/SMS here, and fill() spreads it over the boxes
          autoComplete={i === 0 ? "one-time-code" : "off"}
          maxLength={CODE_LENGTH}
          aria-label={`Digit ${i + 1}`}
          value={digit}
          onChange={(event) => {
            const typed = event.target.value;
            // Typed into a box that already had a digit: keep only the new one
            fill(i, digit && typed.length > 1 && typed.startsWith(digit) ? typed.slice(1) : typed);
          }}
          onKeyDown={(event) => keyDown(i, event)}
          onPaste={(event) => {
            event.preventDefault();
            fill(0, event.clipboardData.getData("text"));
          }}
          onFocus={(event) => event.target.select()}
        />
      ))}
    </div>
  );
}

export default ForgotPasswordPage;
