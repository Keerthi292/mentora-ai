import { useState } from "react";

import ConfirmDeleteModal from "../components/ConfirmDeleteModal";
import FilterPills from "../components/FilterPills";
import FormModal from "../components/FormModal";
import PageAssistant from "../components/PageAssistant";
import ResumeImportModal from "../components/ResumeImportModal";
import { formatStatus, statusOptions } from "../components/StatusBadge";
import useResource from "../hooks/useResource";
import { api } from "../services/api";

// Must match Proficiency and UserSkillStatus in backend/app/schemas.py
const LEVELS = ["beginner", "intermediate", "advanced", "expert"];
const STATUSES = ["want_to_learn", "learning", "acquired"];
const NOT_SET = "not_set"; // filter for skills without a level

const FIELDS = [
  { name: "name", label: "Name", required: true, maxLength: 100, placeholder: "e.g. Python" },
  { name: "category", label: "Category", maxLength: 100, placeholder: "e.g. Programming" },
  {
    name: "proficiency",
    label: "Your level",
    type: "select",
    options: [{ value: "", label: "Not set" }, ...statusOptions(LEVELS)],
  },
  { name: "status", label: "Status", type: "select", options: statusOptions(STATUSES), defaultValue: "learning" },
];

// Skills (the catalog in /api/skills) with your level for each (/api/user-skills)
function Skills() {
  const skills = useResource("/api/skills");
  const levels = useResource("/api/user-skills");
  const [filter, setFilter] = useState("all");
  // null (closed), "new" or the skill being edited
  const [editing, setEditing] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [importing, setImporting] = useState(false);
  const [savingId, setSavingId] = useState(null);
  const [error, setError] = useState("");

  const levelOf = new Map(levels.items.map((us) => [us.skill_id, us]));
  const rows = skills.items.map((skill) => {
    const level = levelOf.get(skill.id);
    return { ...skill, level, status: level?.status ?? NOT_SET };
  });
  const shown = filter === "all" ? rows : rows.filter((row) => row.status === filter);

  const reloadAll = () => Promise.all([skills.reload(), levels.reload()]);

  // Create, change or (with null) remove your level for a skill
  const saveLevel = async (skillId, changes) => {
    const current = levelOf.get(skillId);
    if (!changes) {
      if (current) await api.delete(`/api/user-skills/${current.id}`);
    } else if (current) {
      await api.patch(`/api/user-skills/${current.id}`, changes);
    } else {
      await api.post("/api/user-skills", { skill_id: skillId, ...changes });
    }
  };

  // A dropdown in the table changed
  const changeLevel = async (skillId, changes) => {
    setSavingId(skillId);
    setError("");
    try {
      await saveLevel(skillId, changes);
      await levels.reload();
    } catch (err) {
      setError(err.message);
    } finally {
      setSavingId(null);
    }
  };

  // The add / edit form
  const saveSkill = async ({ proficiency, status, ...skillData }) => {
    const skill =
      editing === "new"
        ? await api.post("/api/skills", skillData)
        : await api.patch(`/api/skills/${editing.id}`, skillData);
    await saveLevel(skill.id, proficiency ? { proficiency, status } : null);
    await reloadAll();
  };

  const deleteSkill = async (skill) => {
    await api.delete(`/api/skills/${skill.id}`); // its level is deleted with it
    await reloadAll();
  };

  const loading = skills.loading && skills.items.length === 0;
  const loadError = skills.error || levels.error;

  return (
    <>
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
        <div>
          <h1 className="h3 mb-0">Skills</h1>
          <div className="text-body-secondary small">What you know, and how well. The mentor uses your levels.</div>
        </div>
        <div className="d-flex flex-wrap gap-2">
          <button type="button" className="btn btn-outline-secondary" onClick={() => setImporting(true)}>
            <i className="bi bi-file-earmark-person me-1" aria-hidden="true" /> Import from resume
          </button>
          <button type="button" className="btn btn-gradient" onClick={() => setEditing("new")}>
            + Add skill
          </button>
        </div>
      </div>

      {rows.length > 0 && (
        <div className="mb-3">
          <FilterPills statuses={[...STATUSES, NOT_SET]} items={rows} value={filter} onChange={setFilter} />
        </div>
      )}

      {loadError && <div className="alert alert-danger">Could not load skills: {loadError}</div>}
      {error && (
        <div className="alert alert-danger d-flex align-items-center gap-2 py-2">
          <span className="flex-grow-1">Could not save the level: {error}</span>
          <button type="button" className="btn-close btn-sm" aria-label="Dismiss" onClick={() => setError("")} />
        </div>
      )}

      {loading ? (
        <div className="text-body-secondary">
          <span className="spinner-border spinner-border-sm me-2" role="status" />
          Loading...
        </div>
      ) : !loadError && rows.length === 0 ? (
        <div className="card card-body text-center text-body-secondary">
          No skills yet. Add your first one, or import them from your resume!
        </div>
      ) : (
        rows.length > 0 && (
          <div className="table-responsive">
            <table className="table table-hover align-middle">
              <thead>
                <tr>
                  <th scope="col">Name</th>
                  <th scope="col">Category</th>
                  <th scope="col">Your level</th>
                  <th scope="col">Status</th>
                  <th scope="col" className="text-end">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {shown.map((skill) => (
                  <tr key={skill.id}>
                    <td className="fw-semibold">{skill.name}</td>
                    <td>{skill.category || <span className="text-body-secondary">-</span>}</td>
                    <td>
                      <select
                        className={`form-select form-select-sm level-select ${skill.level ? "" : "text-body-secondary"}`}
                        aria-label={`Your level in ${skill.name}`}
                        value={skill.level?.proficiency ?? ""}
                        disabled={savingId === skill.id}
                        onChange={(e) =>
                          changeLevel(
                            skill.id,
                            e.target.value ? { proficiency: e.target.value, status: skill.level?.status ?? "learning" } : null
                          )
                        }
                      >
                        <option value="">Set level...</option>
                        {LEVELS.map((level) => (
                          <option key={level} value={level}>
                            {formatStatus(level)}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td>
                      <select
                        className="form-select form-select-sm level-select"
                        aria-label={`Status of ${skill.name}`}
                        value={skill.level?.status ?? ""}
                        disabled={!skill.level || savingId === skill.id}
                        title={skill.level ? undefined : "Set a level first"}
                        onChange={(e) => changeLevel(skill.id, { status: e.target.value })}
                      >
                        {!skill.level && <option value="">-</option>}
                        {STATUSES.map((status) => (
                          <option key={status} value={status}>
                            {formatStatus(status)}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="text-end text-nowrap">
                      <button
                        type="button"
                        className="btn btn-sm btn-outline-primary me-2"
                        onClick={() => setEditing(skill)}
                      >
                        Edit
                      </button>
                      <button type="button" className="btn btn-sm btn-outline-danger" onClick={() => setDeleting(skill)}>
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {shown.length === 0 && <p className="text-body-secondary">No skills with this status.</p>}
          </div>
        )
      )}

      {editing && (
        <FormModal
          key={editing === "new" ? "new" : editing.id}
          title={editing === "new" ? "Add skill" : "Edit skill"}
          submitLabel={editing === "new" ? "Add" : "Save changes"}
          fields={FIELDS}
          initialValues={
            editing === "new"
              ? {}
              : { ...editing, proficiency: editing.level?.proficiency ?? "", status: editing.level?.status ?? "learning" }
          }
          onSubmit={saveSkill}
          onClose={() => setEditing(null)}
        />
      )}

      {deleting && (
        <ConfirmDeleteModal
          itemLabel={deleting.name}
          onConfirm={() => deleteSkill(deleting)}
          onClose={() => setDeleting(null)}
        />
      )}

      {importing && <ResumeImportModal onClose={() => setImporting(false)} onImported={reloadAll} />}

      <PageAssistant page="skills" onChanged={reloadAll} />
    </>
  );
}

export default Skills;
