"""Business rules for importing a resume: read it, show what was found, save what the user picks.

Two steps, so nothing is saved without the user seeing it first:
1. parse_resume: Gemini reads the uploaded file; returns skills and projects,
   each marked if it is already saved.
2. import_resume: saves the items the user kept. Skills already in the catalog
   and projects with the same name are skipped, so importing twice is safe.
"""

import html

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ai.attachments import Attachment
from app.ai.resume import extract_resume
from app.models import Skill
from app.repositories import project_repository, skill_repository, user_skill_repository
from app.schemas import (
    ResumeImportRequest,
    ResumeImportResponse,
    ResumeParseResponse,
    ResumeProject,
    ResumeProjectPreview,
    ResumeSkillPreview,
)
from app.services import upload_service, user_service

# Types Gemini can read a resume from (GIF isn't one of them)
RESUME_TYPES = {"application/pdf", "image/png", "image/jpeg", "image/webp", "text/plain"}


def parse_resume(db: Session, user_id: int, upload_id: str) -> ResumeParseResponse:
    """Skills and projects found in the uploaded resume. Raises LLMError if Gemini fails."""
    files = upload_service.read_uploads(db, [upload_id], user_id)
    if not files:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    upload, data = files[0]
    if upload.content_type not in RESUME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload your resume as a PDF, an image (PNG, JPEG, WebP) or a text file.",
        )

    extracted = extract_resume(Attachment(upload.filename, upload.content_type, data))

    saved_skills = skill_repository.lowercase_names(db)
    saved_projects = project_repository.lowercase_names(db, user_id)
    return ResumeParseResponse(
        skills=[
            ResumeSkillPreview(
                name=s.name,
                category=s.category or None,
                proficiency=s.proficiency,
                already_saved=s.name.lower() in saved_skills,
            )
            for s in extracted.skills
        ],
        projects=[
            ResumeProjectPreview(
                name=p.name,
                description=p.description or None,
                technologies=p.technologies,
                highlights=p.highlights,
                already_saved=p.name.lower() in saved_projects,
            )
            for p in extracted.projects
        ],
    )


def _get_or_create_skill(db: Session, name: str, category: str | None) -> tuple[Skill, bool]:
    """(skill, True if it was just created)."""
    skill = skill_repository.get_skill_by_name(db, name)
    if skill is not None:
        return skill, False
    try:
        return skill_repository.create_skill(db, {"name": name, "category": category}), True
    except IntegrityError:
        # Another request created the same name at the same moment
        db.rollback()
        return skill_repository.get_skill_by_name(db, name), False


def _write_up(project: ResumeProject) -> str | None:
    """The resume's bullet points as the project's write-up (HTML, like the editor makes)."""
    if not project.highlights:
        return None
    items = "".join(f"<li>{html.escape(h)}</li>" for h in project.highlights if h.strip())
    return f"<p><strong>From my resume</strong></p><ul>{items}</ul>" if items else None


def import_resume(db: Session, user_id: int, payload: ResumeImportRequest) -> ResumeImportResponse:
    user_service.ensure_user_exists(db, user_id)

    skills_added = skills_skipped = 0
    seen: set[str] = set()
    for item in payload.skills:
        if item.name.lower() in seen:
            continue
        seen.add(item.name.lower())

        skill, created = _get_or_create_skill(db, item.name, item.category)
        if created:
            skills_added += 1
        else:
            skills_skipped += 1
        # Record the level from the resume, unless the user already set one
        if user_skill_repository.get_by_user_and_skill(db, user_id, skill.id) is None:
            user_skill_repository.create_user_skill(
                db, user_id, {"skill_id": skill.id, "proficiency": item.proficiency, "status": "acquired"}
            )

    projects_added = projects_skipped = 0
    existing = project_repository.lowercase_names(db, user_id)
    for item in payload.projects:
        if item.name.lower() in existing:
            projects_skipped += 1
            continue
        existing.add(item.name.lower())
        technologies = ", ".join(t.strip() for t in item.technologies if t.strip())
        project_repository.create_project(
            db,
            user_id,
            {
                "name": item.name,
                "description": item.description or None,
                "technologies": technologies or None,
                "status": "completed",
                "content": _write_up(item),
            },
        )
        projects_added += 1

    return ResumeImportResponse(
        skills_added=skills_added,
        skills_skipped=skills_skipped,
        projects_added=projects_added,
        projects_skipped=projects_skipped,
    )
