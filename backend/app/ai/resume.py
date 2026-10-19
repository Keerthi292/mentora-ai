"""Reads a resume with Gemini and pulls out the skills and projects in it.

Gemini gets the file itself (PDF or image as bytes, text files as text) and
answers in JSON shaped like `ExtractedResume`. The answer is then tidied up:
spaces trimmed, duplicates removed, lengths clipped to what the database
allows, so the rest of the app can trust it like any other input.
"""

from google.genai import types
from pydantic import BaseModel, Field

from app.ai import llm_client
from app.ai.attachments import Attachment

MAX_SKILLS = 60
MAX_PROJECTS = 15
MAX_HIGHLIGHTS = 6
MAX_TEXT_CHARS = 50_000

PROFICIENCIES = ("beginner", "intermediate", "advanced", "expert")

RESUME_PROMPT = (
    "You read resumes and extract structured data. Only report what the resume "
    "actually says; never invent skills or projects.\n"
    "Skills: every technical or professional skill (languages, frameworks, tools, "
    "databases, cloud, methods, soft skills listed as skills). Use the common name "
    '("JavaScript", not "JS / javascript"), one skill per entry. category is a short '
    'group such as "Programming", "Frontend", "Backend", "Database", "Cloud", "DevOps", '
    '"Data", "AI/ML", "Tools" or "Soft skills". proficiency is one of beginner, '
    "intermediate, advanced, expert: use the resume's own wording if it gives a level, "
    "otherwise estimate it from years of use and how central the skill is to the "
    "person's work (default intermediate).\n"
    "Projects: personal, academic, open-source or work projects that have a name or a "
    "clear title. Do NOT list jobs or employers themselves as projects. description is "
    "one sentence on what it does. technologies lists the tools used. highlights are "
    "up to 6 short bullet points of what the person did or achieved, from the resume.\n"
    "If the file is not a resume, return empty lists."
)


class ExtractedSkill(BaseModel):
    name: str
    category: str = ""
    proficiency: str = "intermediate"


class ExtractedProject(BaseModel):
    name: str
    description: str = ""
    technologies: list[str] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)


class ExtractedResume(BaseModel):
    """The JSON shape Gemini is asked to answer in."""

    skills: list[ExtractedSkill] = Field(default_factory=list)
    projects: list[ExtractedProject] = Field(default_factory=list)


def _clean(text: str, max_length: int) -> str:
    return " ".join(text.split())[:max_length]


def _resume_parts(resume: Attachment) -> list[types.Part]:
    parts = [types.Part(text=f'Extract the skills and projects from this resume ("{resume.filename}").')]
    if resume.content_type == "text/plain":
        text = resume.data.decode("utf-8", errors="replace")[:MAX_TEXT_CHARS]
        parts.append(types.Part(text=f"```\n{text}\n```"))
    else:
        parts.append(types.Part.from_bytes(data=resume.data, mime_type=resume.content_type))
    return parts


def tidy(extracted: ExtractedResume) -> ExtractedResume:
    """Trim, clip and de-duplicate (ignoring case) what Gemini found."""
    skills: dict[str, ExtractedSkill] = {}
    for skill in extracted.skills:
        name = _clean(skill.name, 100)
        if name and name.lower() not in skills:
            proficiency = skill.proficiency.strip().lower()
            skills[name.lower()] = ExtractedSkill(
                name=name,
                category=_clean(skill.category, 100),
                proficiency=proficiency if proficiency in PROFICIENCIES else "intermediate",
            )

    projects: dict[str, ExtractedProject] = {}
    for project in extracted.projects:
        name = _clean(project.name, 255)
        if name and name.lower() not in projects:
            technologies = list(dict.fromkeys(t for t in (_clean(t, 100) for t in project.technologies) if t))
            highlights = [h for h in (_clean(h, 500) for h in project.highlights) if h]
            projects[name.lower()] = ExtractedProject(
                name=name,
                description=_clean(project.description, 1000),
                technologies=technologies,
                highlights=highlights[:MAX_HIGHLIGHTS],
            )

    return ExtractedResume(
        skills=list(skills.values())[:MAX_SKILLS],
        projects=list(projects.values())[:MAX_PROJECTS],
    )


def extract_resume(resume: Attachment) -> ExtractedResume:
    """Skills and projects found in the resume. Raises LLMError if Gemini fails."""
    extracted = llm_client.generate_json(RESUME_PROMPT, _resume_parts(resume), ExtractedResume)
    return tidy(extracted)
