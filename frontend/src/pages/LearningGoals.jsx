import { useEffect, useState } from "react";

import CardMenu from "../components/CardMenu";
import ConfirmDeleteModal from "../components/ConfirmDeleteModal";
import EmptyState from "../components/EmptyState";
import FilterPills from "../components/FilterPills";
import FormModal from "../components/FormModal";
import Modal from "../components/Modal";
import PageAssistant from "../components/PageAssistant";
import ProgressRing from "../components/ProgressRing";
import StatusBadge, { statusOptions } from "../components/StatusBadge";
import useResource from "../hooks/useResource";
import { api } from "../services/api";
import { dueText, formatDate } from "../utils/format";

// Must match LearningGoalStatus in backend/app/schemas.py
const STATUSES = ["active", "paused", "completed", "abandoned"];

const FIELDS = [
  { name: "title", label: "Title", required: true, maxLength: 255, placeholder: "e.g. Learn FastAPI" },
  { name: "description", label: "Description", type: "textarea", placeholder: "What do you want to be able to do?" },
  { name: "status", label: "Status", type: "select", options: statusOptions(STATUSES) },
  { name: "target_date", label: "Target date", type: "date" },
];

// Learning goals as cards, each with a progress ring and an "Update progress" button
function LearningGoals() {
  const { items, loading, error, reload, create, update, remove } = useResource("/api/learning-goals");
  const [filter, setFilter] = useState("all");
  const [editing, setEditing] = useState(null); // null, "new" or a goal
  const [deleting, setDeleting] = useState(null);
  const [progressGoal, setProgressGoal] = useState(null);
  const [celebrate, setCelebrate] = useState(null); // id of a goal that just reached 100%

  const shown = filter === "all" ? items : items.filter((g) => g.status === filter);

  useEffect(() => {
    if (!celebrate) return;
    const timer = setTimeout(() => setCelebrate(null), 2200);
    return () => clearTimeout(timer);
  }, [celebrate]);

  return (
    <>
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
        <div>
          <h1 className="h3 mb-0">Learning Goals</h1>
          <div className="text-body-secondary small">What you're learning, and how far along you are</div>
        </div>
        <button type="button" className="btn btn-gradient" onClick={() => setEditing("new")}>
          <i className="bi bi-plus-lg me-1" aria-hidden="true" /> Add goal
        </button>
      </div>

      {items.length > 0 && (
        <div className="mb-3">
          <FilterPills statuses={STATUSES} items={items} value={filter} onChange={setFilter} />
        </div>
      )}

      {error && <div className="alert alert-danger">Could not load learning goals: {error}</div>}

      {loading && items.length === 0 && !error && (
        <div className="text-body-secondary">
          <span className="spinner-border spinner-border-sm me-2" role="status" /> Loading...
        </div>
      )}

      {!loading && !error && items.length === 0 && (
        <EmptyState
          icon="bi-bullseye"
          text="No learning goals yet. Add one, then log progress as you go."
          action="Add your first goal"
          onAction={() => setEditing("new")}
        />
      )}

      {items.length > 0 && shown.length === 0 && <p className="text-body-secondary">No {filter} goals.</p>}

      <div className="row g-3">
        {shown.map((goal, i) => (
          <div className="col-md-6 col-xl-4" key={goal.id}>
            <GoalCard
              goal={goal}
              index={i}
              celebrating={celebrate === goal.id}
              onProgress={() => setProgressGoal(goal)}
              onEdit={() => setEditing(goal)}
              onDelete={() => setDeleting(goal)}
            />
          </div>
        ))}
      </div>

      {editing && (
        <FormModal
          key={editing === "new" ? "new" : editing.id}
          title={editing === "new" ? "Add goal" : "Edit goal"}
          submitLabel={editing === "new" ? "Add" : "Save changes"}
          fields={FIELDS}
          initialValues={editing === "new" ? {} : editing}
          onSubmit={(data) => (editing === "new" ? create(data) : update(editing.id, data))}
          onClose={() => setEditing(null)}
        />
      )}

      {deleting && (
        <ConfirmDeleteModal itemLabel={deleting.title} onConfirm={() => remove(deleting.id)} onClose={() => setDeleting(null)} />
      )}

      {progressGoal && (
        <ProgressModal
          goal={progressGoal}
          onClose={() => setProgressGoal(null)}
          onSaved={async (reached100) => {
            await reload();
            if (reached100) setCelebrate(progressGoal.id);
          }}
        />
      )}

      <PageAssistant page="goals" onChanged={reload} />
    </>
  );
}

function GoalCard({ goal, index, celebrating, onProgress, onEdit, onDelete }) {
  const due = goal.status === "completed" || goal.status === "abandoned" ? null : dueText(goal.target_date);
  return (
    <div className={`card item-card h-100 ${celebrating ? "celebrating" : ""}`} style={{ animationDelay: `${index * 60}ms` }}>
      {celebrating && <Confetti />}
      <div className="card-body d-flex flex-column">
        <div className="d-flex gap-3 align-items-start">
          <ProgressRing percent={goal.progress_percent} size={66} />
          <div className="flex-grow-1 min-w-0">
            <h2 className="h6 fw-bold mb-1 text-break">{goal.title}</h2>
            <StatusBadge status={goal.status} />
          </div>
          <CardMenu onEdit={onEdit} onDelete={onDelete} label={goal.title} />
        </div>

        {goal.description && <p className="small text-body-secondary mt-3 mb-0 line-clamp-3">{goal.description}</p>}

        <div className="small mt-3 d-flex flex-column gap-1">
          {goal.target_date ? (
            <span className={due ? `text-${due.tone}` : "text-body-secondary"}>
              <i className="bi bi-calendar-event me-1" aria-hidden="true" />
              {formatDate(goal.target_date)}
              {due && <> · {due.text}</>}
            </span>
          ) : (
            <span className="text-body-secondary">
              <i className="bi bi-calendar me-1" aria-hidden="true" />
              No target date
            </span>
          )}
          <span className="text-body-secondary">
            <i className="bi bi-clock-history me-1" aria-hidden="true" />
            {goal.last_progress_at ? `Updated ${formatDate(goal.last_progress_at.slice(0, 10))}` : "No progress logged yet"}
          </span>
        </div>

        <div className="mt-auto pt-3">
          <button type="button" className="btn btn-sm btn-gradient w-100" onClick={onProgress}>
            <i className="bi bi-graph-up-arrow me-1" aria-hidden="true" /> Update progress
          </button>
        </div>
      </div>
    </div>
  );
}

// Slider + note to log progress, and the goal's progress history
function ProgressModal({ goal, onClose, onSaved }) {
  const [percent, setPercent] = useState(goal.progress_percent);
  const [note, setNote] = useState("");
  const [markDone, setMarkDone] = useState(goal.progress_percent === 100 && goal.status !== "completed");
  const [history, setHistory] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const base = `/api/learning-goals/${goal.id}/progress`;

  useEffect(() => {
    api
      .get(base)
      .then((entries) => setHistory(entries.reverse())) // newest first
      .catch((err) => setError(err.message));
  }, [base]);

  const changePercent = (value) => {
    const next = Math.max(0, Math.min(100, value));
    setPercent(next);
    setMarkDone(next === 100 && goal.status !== "completed");
  };

  const save = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await api.post(base, { progress_percent: percent, note: note.trim() || null });
      if (markDone) await api.patch(`/api/learning-goals/${goal.id}`, { status: "completed" });
      await onSaved(percent === 100);
      onClose();
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  };

  const footer = (
    <>
      <button type="button" className="btn btn-outline-secondary" onClick={onClose}>
        Cancel
      </button>
      <button type="submit" form="progress-form" className="btn btn-gradient" disabled={saving}>
        {saving ? "Saving..." : "Save progress"}
      </button>
    </>
  );

  return (
    <Modal title={`Progress: ${goal.title}`} onClose={onClose} footer={footer}>
      <form id="progress-form" onSubmit={save}>
        {error && <div className="alert alert-danger py-2">{error}</div>}

        <div className="d-flex align-items-center gap-3 mb-3">
          <ProgressRing percent={percent} size={84} stroke={8} />
          <div className="flex-grow-1">
            <label htmlFor="progress-range" className="form-label mb-1">
              How far along are you?
            </label>
            <input
              id="progress-range"
              type="range"
              className="form-range"
              min="0"
              max="100"
              step="5"
              value={percent}
              onChange={(e) => changePercent(Number(e.target.value))}
            />
            <div className="d-flex flex-wrap gap-1">
              {[-10, +10, +25].map((step) => (
                <button key={step} type="button" className="btn btn-sm filter-pill" onClick={() => changePercent(percent + step)}>
                  {step > 0 ? `+${step}` : step}%
                </button>
              ))}
              <button type="button" className="btn btn-sm filter-pill" onClick={() => changePercent(100)}>
                Done 🎉
              </button>
            </div>
          </div>
        </div>

        <div className="mb-3">
          <label htmlFor="progress-note" className="form-label">
            Note <span className="text-body-secondary small">(optional)</span>
          </label>
          <textarea
            id="progress-note"
            className="form-control"
            rows={2}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="e.g. Finished the routing chapter"
          />
        </div>

        {percent === 100 && goal.status !== "completed" && (
          <div className="form-check mb-3">
            <input
              id="mark-done"
              className="form-check-input"
              type="checkbox"
              checked={markDone}
              onChange={(e) => setMarkDone(e.target.checked)}
            />
            <label className="form-check-label" htmlFor="mark-done">
              Mark this goal as completed
            </label>
          </div>
        )}
      </form>

      <h3 className="h6 mt-2">History</h3>
      {history === null && !error && <div className="small text-body-secondary">Loading...</div>}
      {history?.length === 0 && <div className="small text-body-secondary">No updates yet. This will be the first!</div>}
      {history?.length > 0 && (
        <ul className="progress-timeline list-unstyled mb-0">
          {history.map((entry) => (
            <li key={entry.id}>
              <span className="fw-semibold">{entry.progress_percent}%</span>
              <span className="text-body-secondary small ms-2">{formatDate(entry.created_at.slice(0, 10))}</span>
              {entry.note && <div className="small">{entry.note}</div>}
            </li>
          ))}
        </ul>
      )}
    </Modal>
  );
}

// A short burst of emoji when a goal reaches 100%
function Confetti() {
  const pieces = ["🎉", "✨", "🎊", "⭐", "🎉", "✨", "🎊", "⭐"];
  return (
    <div className="confetti" aria-hidden="true">
      {pieces.map((piece, i) => (
        <span key={i} style={{ "--angle": `${i * 45}deg`, animationDelay: `${(i % 3) * 60}ms` }}>
          {piece}
        </span>
      ))}
    </div>
  );
}

export default LearningGoals;
