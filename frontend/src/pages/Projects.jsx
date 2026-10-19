import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import EmptyState from "../components/EmptyState";
import FilterPills from "../components/FilterPills";
import FormModal from "../components/FormModal";
import ResumeImportModal from "../components/ResumeImportModal";
import StatusBadge, { statusOptions } from "../components/StatusBadge";
import useResource from "../hooks/useResource";
import { api } from "../services/api";
import { fileUrl } from "../services/uploads";
import { splitList } from "../utils/format";

// Must match ProjectStatus in backend/app/schemas.py
export const STATUSES = ["planned", "in_progress", "completed", "on_hold"];

export const FIELDS = [
  { name: "name", label: "Project name", required: true, maxLength: 255, placeholder: "e.g. Mentora AI" },
  { name: "description", label: "One-line summary", placeholder: "What it does, in a sentence" },
  { name: "technologies", label: "Technologies (comma-separated)", placeholder: "e.g. React, FastAPI, PostgreSQL" },
  { name: "status", label: "Status", type: "select", options: statusOptions(STATUSES) },
];

// The first image and a plain-text preview of a write-up (HTML from the editor)
function preview(html) {
  if (!html) return { image: null, text: "" };
  const doc = new DOMParser().parseFromString(html, "text/html");
  return {
    image: doc.querySelector("img")?.getAttribute("src") ?? null,
    text: doc.body.textContent.replace(/\s+/g, " ").trim(),
  };
}

// Projects as cards; each opens a page with its full write-up
function Projects() {
  const { items, loading, error, reload } = useResource("/api/projects");
  const navigate = useNavigate();
  const [filter, setFilter] = useState("all");
  const [adding, setAdding] = useState(false);
  const [importing, setImporting] = useState(false);

  const shown = filter === "all" ? items : items.filter((p) => p.status === filter);

  // Create the project, then open it ready to write
  const create = async (data) => {
    const project = await api.post("/api/projects", data);
    navigate(`/projects/${project.id}?edit=1`);
  };

  return (
    <>
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
        <div>
          <h1 className="h3 mb-0">Projects</h1>
          <div className="text-body-secondary small">What you've built, with write-ups and screenshots</div>
        </div>
        <div className="d-flex flex-wrap gap-2">
          <button type="button" className="btn btn-outline-secondary" onClick={() => setImporting(true)}>
            <i className="bi bi-file-earmark-person me-1" aria-hidden="true" /> Import from resume
          </button>
          <button type="button" className="btn btn-gradient" onClick={() => setAdding(true)}>
            <i className="bi bi-plus-lg me-1" aria-hidden="true" /> New project
          </button>
        </div>
      </div>

      {items.length > 0 && (
        <div className="mb-3">
          <FilterPills statuses={STATUSES} items={items} value={filter} onChange={setFilter} />
        </div>
      )}

      {error && <div className="alert alert-danger">Could not load projects: {error}</div>}

      {loading && items.length === 0 && !error && (
        <div className="text-body-secondary">
          <span className="spinner-border spinner-border-sm me-2" role="status" /> Loading...
        </div>
      )}

      {!loading && !error && items.length === 0 && (
        <EmptyState
          icon="bi-kanban"
          text="No projects yet. Create one and write about it, with images, like a blog post."
          action="Create your first project"
          onAction={() => setAdding(true)}
        />
      )}

      {items.length > 0 && shown.length === 0 && <p className="text-body-secondary">No projects with this status.</p>}

      <div className="row g-3">
        {shown.map((project, i) => {
          const { image, text } = preview(project.content);
          return (
            <div className="col-md-6 col-xl-4" key={project.id}>
              <Link
                to={`/projects/${project.id}`}
                className="card item-card project-card h-100 text-decoration-none"
                style={{ animationDelay: `${i * 60}ms` }}
              >
                <div className="project-cover">
                  {image ? (
                    <img src={fileUrl(image)} alt="" loading="lazy" />
                  ) : (
                    <i className="bi bi-kanban" aria-hidden="true" />
                  )}
                </div>
                <div className="card-body d-flex flex-column">
                  <div className="d-flex justify-content-between align-items-start gap-2 mb-1">
                    <h2 className="h6 fw-bold mb-0 text-body text-break">{project.name}</h2>
                    <StatusBadge status={project.status} />
                  </div>
                  <p className="small text-body-secondary mb-2 line-clamp-3">
                    {project.description || text || "No write-up yet. Open it to start writing."}
                  </p>
                  <div className="mt-auto d-flex flex-wrap gap-1">
                    {splitList(project.technologies).map((tech) => (
                      <span key={tech} className="badge rounded-pill bg-body-tertiary text-body border">
                        {tech}
                      </span>
                    ))}
                  </div>
                </div>
              </Link>
            </div>
          );
        })}
      </div>

      {adding && (
        <FormModal
          title="New project"
          submitLabel="Create & start writing"
          fields={FIELDS}
          initialValues={{}}
          onSubmit={create}
          onClose={() => setAdding(false)}
        />
      )}

      {importing && <ResumeImportModal onClose={() => setImporting(false)} onImported={reload} />}
    </>
  );
}

export default Projects;
