import { useState } from "react";

import CrudPage from "../components/CrudPage";
import ResumeImportModal from "../components/ResumeImportModal";

// The shared skill catalog (e.g. "Python", "SQL"). Names must be unique.
const FIELDS = [
  { name: "name", label: "Name", required: true, maxLength: 100, placeholder: "e.g. Python" },
  { name: "category", label: "Category", maxLength: 100, placeholder: "e.g. Programming" },
];

const COLUMNS = [
  { header: "Name", render: (skill) => <span className="fw-semibold">{skill.name}</span> },
  { header: "Category", render: (skill) => skill.category || <span className="text-body-secondary">-</span> },
];

function Skills() {
  // The list's reload function while the resume dialog is open, otherwise null
  const [importing, setImporting] = useState(null);

  return (
    <>
      <CrudPage
        title="Skills"
        itemName="skill"
        apiPath="/api/skills"
        fields={FIELDS}
        columns={COLUMNS}
        getLabel={(skill) => skill.name}
        emptyText="No skills yet. Add your first one, or import them from your resume!"
        actions={(reload) => (
          <button type="button" className="btn btn-outline-secondary" onClick={() => setImporting(() => reload)}>
            <i className="bi bi-file-earmark-person me-1" aria-hidden="true" /> Import from resume
          </button>
        )}
      />
      {importing && <ResumeImportModal onClose={() => setImporting(null)} onImported={importing} />}
    </>
  );
}

export default Skills;
