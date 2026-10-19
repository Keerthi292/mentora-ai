import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import CardMenu from "../components/CardMenu";
import ConfirmDeleteModal from "../components/ConfirmDeleteModal";
import EmptyState from "../components/EmptyState";
import FormModal from "../components/FormModal";
import ProgressRing from "../components/ProgressRing";
import useResource from "../hooks/useResource";
import { splitList } from "../utils/format";

// Only what matters: the role, the skills it needs, and optional notes
const FIELDS = [
  { name: "target_role", label: "Target role", required: true, maxLength: 255, placeholder: "e.g. Backend Engineer" },
  { name: "required_skills", label: "Skills needed (comma-separated)", placeholder: "e.g. Python, SQL, Docker" },
  { name: "description", label: "Notes", type: "textarea", placeholder: "Optional: why this role, dream companies..." },
];

// Career goals as live cards: skills needed vs skills you have, edited in place
function CareerGoals() {
  const careers = useResource("/api/career-goals");
  const skills = useResource("/api/skills");
  const navigate = useNavigate();
  const [editing, setEditing] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [busySkill, setBusySkill] = useState(""); // skill being added to the Skills page

  const owned = new Set(skills.items.map((s) => s.name.toLowerCase()));
  const { items, loading, error } = careers;

  // Stay in sync with changes made on other pages or tabs
  useEffect(() => {
    const refresh = () => {
      if (document.visibilityState === "visible") {
        careers.reload();
        skills.reload();
      }
    };
    document.addEventListener("visibilitychange", refresh);
    window.addEventListener("focus", refresh);
    return () => {
      document.removeEventListener("visibilitychange", refresh);
      window.removeEventListener("focus", refresh);
    };
  }, []);

  const addToMySkills = async (name) => {
    setBusySkill(name);
    try {
      await skills.create({ name });
    } catch {
      await skills.reload(); // e.g. it already exists with different casing
    } finally {
      setBusySkill("");
    }
  };

  // Save a card's needed skills right away (no form)
  const saveNeeded = (goal, list) => careers.update(goal.id, { required_skills: list.length ? list.join(", ") : null });

  const askForRoadmap = (goal) => {
    const needed = splitList(goal.required_skills);
    const prompt =
      `Create a step-by-step roadmap for me to become a ${goal.target_role}` +
      (needed.length ? `. Skills needed: ${needed.join(", ")}.` : ".") +
      " Use what you know about my current skills and goals.";
    navigate("/mentor", { state: { prompt } });
  };

  return (
    <>
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
        <div>
          <h1 className="h3 mb-0">Career Goals</h1>
          <div className="text-body-secondary small">The roles you're aiming for, and how ready you are</div>
        </div>
        <button type="button" className="btn btn-gradient" onClick={() => setEditing("new")}>
          <i className="bi bi-plus-lg me-1" aria-hidden="true" /> Add target role
        </button>
      </div>

      {error && <div className="alert alert-danger">Could not load career goals: {error}</div>}

      {loading && items.length === 0 && !error && (
        <div className="text-body-secondary">
          <span className="spinner-border spinner-border-sm me-2" role="status" /> Loading...
        </div>
      )}

      {!loading && !error && items.length === 0 && (
        <EmptyState
          icon="bi-briefcase"
          text="No career goals yet. Add the role you're aiming for and the skills it needs."
          action="Add your target role"
          onAction={() => setEditing("new")}
        />
      )}

      <div className="row g-3">
        {items.map((goal, i) => (
          <div className="col-lg-6" key={goal.id}>
            <CareerCard
              goal={goal}
              index={i}
              owned={owned}
              busySkill={busySkill}
              onAddToMySkills={addToMySkills}
              onSaveNeeded={(list) => saveNeeded(goal, list)}
              onRoadmap={() => askForRoadmap(goal)}
              onEdit={() => setEditing(goal)}
              onDelete={() => setDeleting(goal)}
            />
          </div>
        ))}
      </div>

      {editing && (
        <FormModal
          key={editing === "new" ? "new" : editing.id}
          title={editing === "new" ? "Add target role" : "Edit target role"}
          submitLabel={editing === "new" ? "Add" : "Save changes"}
          fields={FIELDS}
          initialValues={editing === "new" ? {} : editing}
          onSubmit={(data) => (editing === "new" ? careers.create(data) : careers.update(editing.id, data))}
          onClose={() => setEditing(null)}
        />
      )}

      {deleting && (
        <ConfirmDeleteModal
          itemLabel={deleting.target_role}
          onConfirm={() => careers.remove(deleting.id)}
          onClose={() => setDeleting(null)}
        />
      )}
    </>
  );
}

function CareerCard({ goal, index, owned, busySkill, onAddToMySkills, onSaveNeeded, onRoadmap, onEdit, onDelete }) {
  // Shown immediately; saved in the background (rolled back if saving fails)
  const [needed, setNeeded] = useState(() => splitList(goal.required_skills));
  const [newSkill, setNewSkill] = useState("");
  const [error, setError] = useState("");

  // Follow saved changes (e.g. after editing in the form or another tab)
  useEffect(() => setNeeded(splitList(goal.required_skills)), [goal.required_skills]);

  const have = needed.filter((s) => owned.has(s.toLowerCase()));
  const readiness = needed.length ? Math.round((have.length / needed.length) * 100) : 0;

  const change = async (next) => {
    const previous = needed;
    setNeeded(next);
    setError("");
    try {
      await onSaveNeeded(next);
    } catch (err) {
      setNeeded(previous);
      setError(err.message);
    }
  };

  const addNeeded = (event) => {
    event.preventDefault();
    const names = splitList(newSkill).filter((n) => !needed.some((s) => s.toLowerCase() === n.toLowerCase()));
    setNewSkill("");
    if (names.length) change([...needed, ...names]);
  };

  return (
    <div className="card item-card h-100" style={{ animationDelay: `${index * 60}ms` }}>
      <div className="card-body d-flex flex-column">
        <div className="d-flex gap-3 align-items-start">
          <ProgressRing percent={readiness} size={70} label={`${have.length} of ${needed.length} skills ready`} />
          <div className="flex-grow-1 min-w-0">
            <h2 className="h5 fw-bold mb-1 text-break">{goal.target_role}</h2>
            <div className="small text-body-secondary">
              {needed.length
                ? readiness === 100
                  ? "You have every skill on your list 🎉"
                  : `${have.length} of ${needed.length} skills ready`
                : "Add the skills this role needs"}
            </div>
          </div>
          <CardMenu onEdit={onEdit} onDelete={onDelete} label={goal.target_role} />
        </div>

        {goal.description && <p className="small text-body-secondary mt-3 mb-0 line-clamp-3">{goal.description}</p>}

        <div className="skills-roadmap mt-3">
          <div className="d-flex flex-wrap gap-1 mb-2">
            {needed.map((skill) => {
              const has = owned.has(skill.toLowerCase());
              return (
                <span key={skill} className={`skill-chip ${has ? "have" : "missing"}`}>
                  {has ? (
                    <i className="bi bi-check-circle-fill me-1" aria-hidden="true" />
                  ) : (
                    <button
                      type="button"
                      className="chip-action"
                      onClick={() => onAddToMySkills(skill)}
                      disabled={busySkill === skill}
                      aria-label={`I have ${skill}: add it to my Skills`}
                      title="I have this: add to my Skills"
                    >
                      <i className={`bi ${busySkill === skill ? "bi-hourglass-split" : "bi-plus-circle"}`} aria-hidden="true" />
                    </button>
                  )}
                  {skill}
                  <button
                    type="button"
                    className="chip-action ms-1"
                    onClick={() => change(needed.filter((s) => s !== skill))}
                    aria-label={`Remove ${skill} from this role`}
                    title="Remove from this role"
                  >
                    <i className="bi bi-x" aria-hidden="true" />
                  </button>
                </span>
              );
            })}
          </div>
          <form className="d-flex gap-1" onSubmit={addNeeded}>
            <input
              className="form-control form-control-sm"
              value={newSkill}
              onChange={(e) => setNewSkill(e.target.value)}
              placeholder="Add a needed skill (e.g. Docker)"
              aria-label={`Add a skill needed for ${goal.target_role}`}
              maxLength={100}
            />
            <button type="submit" className="btn btn-sm btn-outline-secondary" disabled={!newSkill.trim()} aria-label="Add skill">
              <i className="bi bi-plus-lg" aria-hidden="true" />
            </button>
          </form>
          {error && <div className="small text-danger mt-1">{error}</div>}
        </div>

        <div className="mt-auto pt-3">
          <button type="button" className="btn btn-sm btn-outline-secondary w-100 roadmap-btn" onClick={onRoadmap}>
            <i className="bi bi-signpost-split me-1" aria-hidden="true" /> Ask Mentora for a roadmap
          </button>
        </div>
      </div>
    </div>
  );
}

export default CareerGoals;
