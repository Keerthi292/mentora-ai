import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";

import ConfirmDeleteModal from "../components/ConfirmDeleteModal";
import FormModal from "../components/FormModal";
import RichEditor from "../components/RichEditor";
import StatusBadge from "../components/StatusBadge";
import { api } from "../services/api";
import { splitList } from "../utils/format";
import { FIELDS } from "./Projects";

// One project: its details and a rich write-up (text, headings, lists, images)
function ProjectDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [project, setProject] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [editing, setEditing] = useState(searchParams.get("edit") === "1");
  const [draft, setDraft] = useState(null); // write-up being edited (stored HTML)
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [savedAt, setSavedAt] = useState(null);
  const [editingDetails, setEditingDetails] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const dirty = editing && draft !== null && draft !== (project?.content ?? "");

  useEffect(() => {
    api
      .get(`/api/projects/${id}`)
      .then(setProject)
      .catch((err) => setLoadError(err.message));
  }, [id]);

  // Drop "?edit=1" from the URL once we've read it
  useEffect(() => {
    if (searchParams.has("edit")) setSearchParams({}, { replace: true });
  }, [searchParams, setSearchParams]);

  // Warn before leaving the browser tab with unsaved changes
  useEffect(() => {
    if (!dirty) return;
    const warn = (event) => event.preventDefault();
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  const save = useCallback(async () => {
    if (!dirty || saving) return;
    setSaving(true);
    setSaveError("");
    try {
      // An empty editor gives "<p></p>": store that as no write-up
      const content = draft === "<p></p>" ? null : draft;
      const updated = await api.patch(`/api/projects/${id}`, { content });
      setProject(updated);
      setDraft(updated.content ?? "");
      setSavedAt(new Date());
    } catch (err) {
      setSaveError(err.message);
    } finally {
      setSaving(false);
    }
  }, [dirty, saving, draft, id]);

  // Ctrl/Cmd + S saves while editing
  useEffect(() => {
    if (!editing) return;
    const onKey = (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
        event.preventDefault();
        save();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [editing, save]);

  const finishEditing = () => {
    if (dirty && !window.confirm("Discard your unsaved changes?")) return;
    setEditing(false);
    setDraft(null);
    setSaveError("");
  };

  if (loadError) {
    return (
      <div className="alert alert-danger">
        Could not load this project: {loadError} <Link to="/projects">Back to projects</Link>
      </div>
    );
  }
  if (!project) {
    return (
      <div className="text-body-secondary">
        <span className="spinner-border spinner-border-sm me-2" role="status" /> Loading...
      </div>
    );
  }

  return (
    <div className="project-detail mx-auto">
      <Link to="/projects" className="small text-decoration-none">
        <i className="bi bi-arrow-left me-1" aria-hidden="true" /> All projects
      </Link>

      <div className="d-flex flex-wrap justify-content-between align-items-start gap-2 mt-2 mb-3">
        <div className="min-w-0">
          <h1 className="h2 fw-bold mb-1 text-break">{project.name}</h1>
          {project.description && <p className="lead text-body-secondary mb-2">{project.description}</p>}
          <div className="d-flex flex-wrap align-items-center gap-1">
            <StatusBadge status={project.status} />
            {splitList(project.technologies).map((tech) => (
              <span key={tech} className="badge rounded-pill bg-body-tertiary text-body border">
                {tech}
              </span>
            ))}
          </div>
        </div>
        <div className="d-flex gap-2">
          <button type="button" className="btn btn-sm btn-outline-secondary" onClick={() => setEditingDetails(true)}>
            <i className="bi bi-sliders me-1" aria-hidden="true" /> Details
          </button>
          <button type="button" className="btn btn-sm btn-outline-danger" onClick={() => setDeleting(true)}>
            <i className="bi bi-trash3 me-1" aria-hidden="true" /> Delete
          </button>
        </div>
      </div>

      <div className="card write-up-card">
        <div className="card-header d-flex flex-wrap justify-content-between align-items-center gap-2 bg-transparent">
          <span className="fw-semibold">
            <i className="bi bi-journal-richtext me-2 text-gradient-icon" aria-hidden="true" />
            Write-up
          </span>
          {editing ? (
            <div className="d-flex align-items-center gap-2">
              <span className="small text-body-secondary">
                {saving ? "Saving..." : dirty ? "Unsaved changes" : savedAt ? "All changes saved" : ""}
              </span>
              <button type="button" className="btn btn-sm btn-outline-secondary" onClick={finishEditing}>
                Done
              </button>
              <button type="button" className="btn btn-sm btn-gradient" onClick={save} disabled={!dirty || saving}>
                <i className="bi bi-check2 me-1" aria-hidden="true" /> Save
              </button>
            </div>
          ) : (
            <button
              type="button"
              className="btn btn-sm btn-gradient"
              onClick={() => {
                setDraft(project.content ?? "");
                setEditing(true);
              }}
            >
              <i className="bi bi-pencil me-1" aria-hidden="true" /> {project.content ? "Edit write-up" : "Start writing"}
            </button>
          )}
        </div>

        {saveError && <div className="alert alert-danger m-3 mb-0 py-2">{saveError}</div>}

        {!editing && !project.content ? (
          <div className="card-body text-center text-body-secondary py-5">
            <i className="bi bi-journal-plus display-6" aria-hidden="true" />
            <p className="mt-2 mb-0">No write-up yet. Describe what you built, how, and what you learned, and add screenshots.</p>
          </div>
        ) : (
          <RichEditor
            // A new key shows the saved version again after "Done"
            key={editing ? "edit" : `view-${project.content?.length ?? 0}`}
            content={editing ? (draft ?? project.content) : project.content}
            editable={editing}
            onChange={setDraft}
            placeholder="What did you build? Why? How does it work? What did you learn? Paste or drop screenshots anywhere."
          />
        )}
      </div>
      {editing && (
        <div className="small text-body-secondary mt-2">
          Tip: paste or drag images straight into the text. Ctrl+S saves.
        </div>
      )}

      {editingDetails && (
        <FormModal
          title="Project details"
          fields={FIELDS}
          initialValues={project}
          onSubmit={async (data) => setProject(await api.patch(`/api/projects/${id}`, data))}
          onClose={() => setEditingDetails(false)}
        />
      )}

      {deleting && (
        <ConfirmDeleteModal
          itemLabel={project.name}
          onConfirm={async () => {
            await api.delete(`/api/projects/${id}`);
            navigate("/projects");
          }}
          onClose={() => setDeleting(false)}
        />
      )}
    </div>
  );
}

export default ProjectDetail;
