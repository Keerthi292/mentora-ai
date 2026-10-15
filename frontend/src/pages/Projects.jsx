import CrudPage from "../components/CrudPage";
import StatusBadge, { statusOptions } from "../components/StatusBadge";

// Must match ProjectStatus in backend/app/schemas.py
const STATUSES = ["planned", "in_progress", "completed", "on_hold"];

const FIELDS = [
  { name: "name", label: "Name", required: true, maxLength: 255, placeholder: "e.g. Portfolio website" },
  { name: "description", label: "Description", type: "textarea" },
  { name: "technologies", label: "Technologies", placeholder: "Comma-separated, e.g. React, FastAPI" },
  { name: "status", label: "Status", type: "select", options: statusOptions(STATUSES) },
];

// "React, FastAPI" -> ["React", "FastAPI"]
function splitTechnologies(text) {
  return (text || "").split(",").map((t) => t.trim()).filter(Boolean);
}

const COLUMNS = [
  {
    header: "Project",
    render: (project) => (
      <>
        <div className="fw-semibold">{project.name}</div>
        {project.description && <div className="small text-body-secondary">{project.description}</div>}
      </>
    ),
  },
  {
    header: "Technologies",
    render: (project) =>
      splitTechnologies(project.technologies).map((tech) => (
        <span key={tech} className="badge rounded-pill text-bg-light border me-1">
          {tech}
        </span>
      )),
  },
  { header: "Status", render: (project) => <StatusBadge status={project.status} /> },
];

function Projects() {
  return (
    <CrudPage
      title="Projects"
      itemName="project"
      apiPath="/api/projects"
      fields={FIELDS}
      columns={COLUMNS}
      getLabel={(project) => project.name}
      emptyText="No projects yet. Add something you're building!"
    />
  );
}

export default Projects;
