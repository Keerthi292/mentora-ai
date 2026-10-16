import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import BotAvatar from "../components/BotAvatar";
import StatusBadge from "../components/StatusBadge";
import { api } from "../services/api";
import { dueText, formatDate } from "../utils/format";

const TIP_KEY = "mentora.dailyTip"; // { date: "YYYY-MM-DD", tip }

const todayKey = () => new Date().toLocaleDateString("en-CA"); // local "YYYY-MM-DD"

function greeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

// Overview of skills, goals, career and projects, plus a personal AI tip
function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/api/dashboard")
      .then(setData)
      .catch((err) => setError(err.message));
  }, []);

  const counts = data?.counts;
  const stats = [
    { to: "/skills", label: "Skills", icon: "bi-stars", value: counts?.skills, detail: "in your list" },
    {
      to: "/goals",
      label: "Learning goals",
      icon: "bi-bullseye",
      value: counts?.learning_goals,
      detail: `${counts?.active_learning_goals ?? 0} active`,
    },
    {
      to: "/career",
      label: "Career goals",
      icon: "bi-briefcase",
      value: counts?.career_goals,
      detail: counts?.career_goals === 1 ? "target role" : "target roles",
    },
    {
      to: "/projects",
      label: "Projects",
      icon: "bi-kanban",
      value: counts?.projects,
      detail: `${counts?.projects_in_progress ?? 0} in progress`,
    },
  ];

  return (
    <>
      <div className="d-flex align-items-center gap-3 mb-4">
        <BotAvatar size={52} float />
        <div>
          <h1 className="h3 mb-0">
            {greeting()}! <span className="wave" aria-hidden="true">👋</span>
          </h1>
          <div className="text-body-secondary small">
            {new Date().toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" })}
          </div>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger">
          <i className="bi bi-wifi-off me-2" aria-hidden="true" />
          Could not load your dashboard: {error}
        </div>
      )}

      <div className="row g-3 mb-4">
        {stats.map((stat, i) => (
          <div className="col-6 col-lg-3" key={stat.to}>
            <Link to={stat.to} className="stat-card card h-100 text-decoration-none" style={{ animationDelay: `${i * 70}ms` }}>
              <div className="card-body">
                <div className="d-flex justify-content-between align-items-start">
                  <span className="suggestion-icon">
                    <i className={`bi ${stat.icon}`} aria-hidden="true" />
                  </span>
                  <i className="bi bi-arrow-up-right stat-arrow text-body-secondary" aria-hidden="true" />
                </div>
                <div className="stat-value mt-3">
                  {stat.value === undefined ? <span className="placeholder col-4 rounded" /> : <CountUp value={stat.value} />}
                </div>
                <div className="fw-semibold text-body">{stat.label}</div>
                <div className="small text-body-secondary">{data ? stat.detail : " "}</div>
              </div>
            </Link>
          </div>
        ))}
      </div>

      <div className="row g-3">
        <div className="col-lg-5 order-lg-last">
          <TipCard />
        </div>
        <div className="col-lg-7">
          <GoalProgress goals={data?.goals} />
        </div>
      </div>
    </>
  );
}

// Counts up from 0 to `value` (or shows it at once if the user prefers less motion)
function CountUp({ value, duration = 800 }) {
  const [shown, setShown] = useState(0);

  useEffect(() => {
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches || value === 0) {
      setShown(value);
      return;
    }
    let frame;
    const start = performance.now();
    const step = (now) => {
      const t = Math.min((now - start) / duration, 1);
      setShown(Math.round(value * (1 - (1 - t) ** 3))); // ease-out
      if (t < 1) frame = requestAnimationFrame(step);
    };
    frame = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frame);
  }, [value, duration]);

  return shown;
}

function GoalProgress({ goals }) {
  return (
    <div className="card h-100">
      <div className="card-body">
        <div className="d-flex justify-content-between align-items-center mb-3">
          <h2 className="h5 mb-0">
            <i className="bi bi-graph-up-arrow me-2 text-gradient-icon" aria-hidden="true" />
            Learning progress
          </h2>
          <Link to="/goals" className="small">
            All goals <i className="bi bi-chevron-right" aria-hidden="true" />
          </Link>
        </div>

        {goals === undefined && (
          <div className="placeholder-glow">
            {[0, 1, 2].map((i) => (
              <div key={i} className="mb-3">
                <span className="placeholder col-6 rounded mb-2" />
                <span className="placeholder col-12 rounded" style={{ height: 10 }} />
              </div>
            ))}
          </div>
        )}

        {goals?.length === 0 && (
          <div className="text-center py-4">
            <i className="bi bi-flag display-6 text-body-secondary" aria-hidden="true" />
            <p className="text-body-secondary mt-2 mb-3">No learning goals yet. Add one to track your progress here.</p>
            <Link to="/goals" className="btn btn-gradient btn-sm">
              <i className="bi bi-plus-lg me-1" aria-hidden="true" /> Add a goal
            </Link>
          </div>
        )}

        {goals?.map((goal, i) => {
          const due = goal.status === "completed" ? null : dueText(goal.target_date);
          return (
            <div key={goal.id} className="goal-row mb-3">
              <div className="d-flex justify-content-between align-items-center gap-2 mb-1">
                <span className="fw-semibold text-truncate">{goal.title}</span>
                <span className="d-flex align-items-center gap-2 flex-shrink-0">
                  <StatusBadge status={goal.status} />
                  <span className="fw-semibold small">{goal.progress_percent}%</span>
                </span>
              </div>
              <div
                className="progress goal-progress"
                role="progressbar"
                aria-label={`${goal.title} progress`}
                aria-valuenow={goal.progress_percent}
                aria-valuemin="0"
                aria-valuemax="100"
              >
                <div
                  className="progress-bar goal-progress-bar"
                  style={{ "--target": `${goal.progress_percent}%`, animationDelay: `${i * 90}ms` }}
                />
              </div>
              <div className="small text-body-secondary mt-1">
                {due ? (
                  <span className={`text-${due.tone}`}>
                    <i className="bi bi-calendar-event me-1" aria-hidden="true" />
                    {formatDate(goal.target_date)} · {due.text}
                  </span>
                ) : goal.target_date ? (
                  <>Target {formatDate(goal.target_date)}</>
                ) : (
                  "No target date"
                )}
                {goal.last_update && <> · updated {formatDate(goal.last_update.slice(0, 10))}</>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// One personal tip a day from the mentor (Gemini). Cached in this browser for the
// day so it doesn't use API quota on every visit; "New tip" asks for another.
function TipCard() {
  const [tip, setTip] = useState(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(TIP_KEY));
      return saved?.date === todayKey() ? saved.tip : "";
    } catch {
      return "";
    }
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchTip = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await api.get("/api/ai/tip");
      setTip(data.tip);
      try {
        localStorage.setItem(TIP_KEY, JSON.stringify({ date: todayKey(), tip: data.tip }));
      } catch {
        // storage blocked: the tip just isn't cached
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // First visit of the day: ask for a tip. The ref stops React's development
  // double-run (StrictMode) from asking Gemini twice.
  const requestedRef = useRef(false);
  useEffect(() => {
    if (tip || requestedRef.current) return;
    requestedRef.current = true;
    fetchTip();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="card tip-card h-100">
      <div className="card-body d-flex flex-column">
        <div className="d-flex align-items-center gap-2 mb-3">
          <BotAvatar size={40} thinking={loading} sparkles={!loading && !!tip} />
          <div>
            <h2 className="h5 mb-0">Mentora's tip for today</h2>
            <div className="small text-body-secondary">Based on your goals and skills</div>
          </div>
        </div>

        <div className="flex-grow-1" aria-live="polite">
          {loading && (
            <div className="placeholder-glow">
              <span className="placeholder col-12 rounded mb-2" />
              <span className="placeholder col-9 rounded" />
            </div>
          )}
          {!loading && error && (
            <div className="alert alert-danger small py-2 mb-0">
              <i className="bi bi-exclamation-triangle me-1" aria-hidden="true" />
              {error}
            </div>
          )}
          {!loading && !error && tip && <p className="tip-text mb-0">{tip}</p>}
        </div>

        <div className="d-flex flex-wrap gap-2 mt-3">
          <button type="button" className="btn btn-sm btn-outline-secondary" onClick={fetchTip} disabled={loading}>
            <i className={`bi bi-arrow-repeat me-1 ${loading ? "spin" : ""}`} aria-hidden="true" />
            {error ? "Try again" : "New tip"}
          </button>
          <Link to="/mentor" className="btn btn-sm btn-gradient">
            <i className="bi bi-chat-heart me-1" aria-hidden="true" />
            Talk to Mentora
          </Link>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
