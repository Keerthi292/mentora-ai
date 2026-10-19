import { useRef, useState } from "react";

import { api } from "../services/api";
import { checkFile, deleteUpload, uploadFile } from "../services/uploads";
import Modal from "./Modal";

// Must match RESUME_TYPES in backend/app/services/resume_service.py
const ACCEPTED_RESUMES = "application/pdf,image/png,image/jpeg,image/webp,.txt,.md";

/**
 * Upload a resume, let the AI find the skills and projects in it, then pick
 * which ones to save. Nothing is saved until "Import" is clicked.
 *
 * `onImported()` is called after saving, so the page can reload its list.
 */
function ResumeImportModal({ onClose, onImported }) {
  // "pick" -> "reading" -> "review" -> "importing" -> "done"
  const [step, setStep] = useState("pick");
  const [error, setError] = useState("");
  const [progress, setProgress] = useState(0);
  const [found, setFound] = useState({ skills: [], projects: [] });
  // Names of the items that will be imported
  const [keepSkills, setKeepSkills] = useState(new Set());
  const [keepProjects, setKeepProjects] = useState(new Set());
  const [result, setResult] = useState(null);
  const inputRef = useRef(null);

  const readResume = async (file) => {
    if (!file) return;
    const problem = checkFile(file);
    if (problem) {
      setError(problem);
      return;
    }
    setError("");
    setProgress(0);
    setStep("reading");
    let upload = null;
    try {
      upload = await uploadFile(file, { onProgress: setProgress });
      const data = await api.post("/api/resume/parse", { upload_id: upload.id });
      setFound(data);
      // Pre-select everything that isn't saved yet
      setKeepSkills(new Set(data.skills.filter((s) => !s.already_saved).map((s) => s.name)));
      setKeepProjects(new Set(data.projects.filter((p) => !p.already_saved).map((p) => p.name)));
      setStep("review");
    } catch (err) {
      setError(err.message);
      setStep("pick");
    } finally {
      // The file was only needed for reading it
      if (upload) deleteUpload(upload.id);
    }
  };

  const toggle = (setter, name) =>
    setter((current) => {
      const next = new Set(current);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });

  const importSelected = async () => {
    setStep("importing");
    setError("");
    try {
      const strip = ({ already_saved: _saved, ...item }) => item;
      const data = await api.post("/api/resume/import", {
        skills: found.skills.filter((s) => keepSkills.has(s.name)).map(strip),
        projects: found.projects.filter((p) => keepProjects.has(p.name)).map(strip),
      });
      setResult(data);
      setStep("done");
      onImported?.();
    } catch (err) {
      setError(err.message);
      setStep("review");
    }
  };

  const selectedCount = keepSkills.size + keepProjects.size;
  const nothingFound = found.skills.length === 0 && found.projects.length === 0;

  const footer =
    step === "review" ? (
      <>
        <button type="button" className="btn btn-outline-secondary me-auto" onClick={() => setStep("pick")}>
          Use another file
        </button>
        <button type="button" className="btn btn-outline-secondary" onClick={onClose}>
          Cancel
        </button>
        <button type="button" className="btn btn-gradient" disabled={selectedCount === 0} onClick={importSelected}>
          Import {selectedCount} item{selectedCount === 1 ? "" : "s"}
        </button>
      </>
    ) : step === "importing" ? (
      <button type="button" className="btn btn-gradient" disabled>
        <span className="spinner-border spinner-border-sm me-2" role="status" /> Saving...
      </button>
    ) : step === "done" ? (
      <button type="button" className="btn btn-gradient" onClick={onClose}>
        Done
      </button>
    ) : null;

  return (
    <Modal title="Import from resume" onClose={onClose} footer={footer} size="lg">
      {error && <div className="alert alert-danger py-2">{error}</div>}

      {step === "pick" && (
        <div
          className="resume-drop"
          role="button"
          tabIndex={0}
          onClick={() => inputRef.current?.click()}
          onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && inputRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            readResume(e.dataTransfer.files[0]);
          }}
        >
          <i className="bi bi-file-earmark-person fs-1 text-gradient-icon" aria-hidden="true" />
          <div className="fw-semibold mt-2">Drop your resume here, or click to choose a file</div>
          <div className="small text-body-secondary">
            PDF, image (PNG, JPEG, WebP) or text file. The AI mentor finds your skills and projects; you choose what
            to save.
          </div>
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED_RESUMES}
            hidden
            onChange={(e) => {
              readResume(e.target.files[0]);
              e.target.value = "";
            }}
          />
        </div>
      )}

      {step === "reading" && (
        <div className="text-center py-5">
          <span className="spinner-border text-primary mb-3" role="status" />
          <div className="fw-semibold">{progress < 1 ? `Uploading... ${Math.round(progress * 100)}%` : "Reading your resume..."}</div>
          <div className="small text-body-secondary">This usually takes a few seconds.</div>
        </div>
      )}

      {(step === "review" || step === "importing") && nothingFound && (
        <p className="text-body-secondary text-center py-4 mb-0">
          No skills or projects were found in this file. Is it a resume?
        </p>
      )}

      {(step === "review" || step === "importing") && !nothingFound && (
        <fieldset disabled={step === "importing"}>
          {found.skills.length > 0 && (
            <section className="mb-4">
              <div className="d-flex justify-content-between align-items-baseline mb-2">
                <h3 className="h6 mb-0">
                  Skills <span className="text-body-secondary fw-normal">({found.skills.length})</span>
                </h3>
                <SelectAll items={found.skills} keep={keepSkills} setKeep={setKeepSkills} />
              </div>
              <div className="d-flex flex-wrap gap-2">
                {found.skills.map((skill) => {
                  const on = keepSkills.has(skill.name);
                  return (
                    <button
                      key={skill.name}
                      type="button"
                      className={`skill-chip resume-chip ${on ? "have" : ""}`}
                      aria-pressed={on}
                      disabled={skill.already_saved}
                      title={skill.already_saved ? "Already on your Skills page" : skill.category || undefined}
                      onClick={() => toggle(setKeepSkills, skill.name)}
                    >
                      <i className={`bi ${skill.already_saved ? "bi-check2-all" : on ? "bi-check-lg" : "bi-plus-lg"} me-1`} aria-hidden="true" />
                      {skill.name}
                      <span className="text-body-secondary ms-1">· {skill.already_saved ? "saved" : skill.proficiency}</span>
                    </button>
                  );
                })}
              </div>
            </section>
          )}

          {found.projects.length > 0 && (
            <section>
              <div className="d-flex justify-content-between align-items-baseline mb-2">
                <h3 className="h6 mb-0">
                  Projects <span className="text-body-secondary fw-normal">({found.projects.length})</span>
                </h3>
                <SelectAll items={found.projects} keep={keepProjects} setKeep={setKeepProjects} />
              </div>
              <div className="d-flex flex-column gap-2">
                {found.projects.map((project) => (
                  <label
                    key={project.name}
                    className={`card card-body py-2 resume-project ${project.already_saved ? "opacity-50" : ""}`}
                  >
                    <div className="d-flex gap-2">
                      <input
                        type="checkbox"
                        className="form-check-input mt-1 flex-shrink-0"
                        checked={keepProjects.has(project.name)}
                        disabled={project.already_saved}
                        onChange={() => toggle(setKeepProjects, project.name)}
                      />
                      <div className="min-w-0">
                        <div className="fw-semibold text-break">
                          {project.name}
                          {project.already_saved && (
                            <span className="badge bg-body-tertiary text-body border ms-2">already saved</span>
                          )}
                        </div>
                        {project.description && <div className="small text-body-secondary">{project.description}</div>}
                        {project.technologies.length > 0 && (
                          <div className="d-flex flex-wrap gap-1 mt-1">
                            {project.technologies.map((tech) => (
                              <span key={tech} className="badge rounded-pill bg-body-tertiary text-body border">
                                {tech}
                              </span>
                            ))}
                          </div>
                        )}
                        {project.highlights.length > 0 && (
                          <ul className="small mb-0 mt-1 ps-3">
                            {project.highlights.map((h) => (
                              <li key={h}>{h}</li>
                            ))}
                          </ul>
                        )}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
              <div className="small text-body-secondary mt-2">
                Projects are saved as completed, with these bullet points as their write-up. You can edit them later.
              </div>
            </section>
          )}
        </fieldset>
      )}

      {step === "done" && result && (
        <div className="text-center py-4">
          <i className="bi bi-check-circle-fill fs-1 text-success" aria-hidden="true" />
          <div className="fw-semibold mt-2">Imported from your resume</div>
          <div className="text-body-secondary">
            {result.skills_added} new skill{result.skills_added === 1 ? "" : "s"}, {result.projects_added} new project
            {result.projects_added === 1 ? "" : "s"}
            {result.skills_skipped + result.projects_skipped > 0 &&
              ` (${result.skills_skipped + result.projects_skipped} already saved, skipped)`}
          </div>
        </div>
      )}
    </Modal>
  );
}

// "Select all" / "Select none" for the items that aren't saved yet
function SelectAll({ items, keep, setKeep }) {
  const selectable = items.filter((item) => !item.already_saved).map((item) => item.name);
  if (selectable.length === 0) return null;
  const allOn = selectable.every((name) => keep.has(name));
  return (
    <button
      type="button"
      className="btn btn-link btn-sm p-0"
      onClick={() => setKeep(new Set(allOn ? [] : selectable))}
    >
      Select {allOn ? "none" : "all"}
    </button>
  );
}

export default ResumeImportModal;
