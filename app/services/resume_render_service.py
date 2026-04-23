import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from docxtpl import DocxTemplate


_logger = logging.getLogger(__name__)

_REQUIRED_FIELDS = {
    "name",
    "contact_number",
    "links",
    "summary",
    "skills",
    "experience",
    "projects",
    "education",
}


class ResumeRenderValidationError(ValueError):
    """Raised when the render request payload is invalid."""


class ResumeRenderFailedError(RuntimeError):
    """Raised when DOCX rendering or PDF conversion fails."""


@dataclass
class RenderedDocxArtifact:
    docx_path: str
    temp_dir: tempfile.TemporaryDirectory[str]


class _CallableList(list[Any]):
    """List that is also callable to support template patterns like values and values()."""

    def __call__(self) -> "_CallableList":
        return self


class _TemplateMapping:
    """Mapping wrapper that is template-friendly for dot-access and dict-like helpers."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    def __getattribute__(self, name: str) -> Any:
        # Prefer payload keys over helper attributes so template fields like
        # `skill.items` resolve to the actual resume value, not mapping helpers.
        if name not in {"_data", "__class__", "__dict__", "__weakref__"}:
            data = object.__getattribute__(self, "_data")
            if isinstance(data, dict) and name in data:
                return _to_template_context(data[name])
        return object.__getattribute__(self, name)

    def __getitem__(self, key: str) -> Any:
        return _to_template_context(self._data[key])

    def __iter__(self):
        for key in self._data:
            yield key

    def __len__(self) -> int:
        return len(self._data)

    @property
    def keys(self) -> _CallableList:
        return _CallableList([_to_template_context(v) for v in self._data.keys()])

    @property
    def values(self) -> _CallableList:
        return _CallableList([_to_template_context(v) for v in self._data.values()])

    @property
    def items(self) -> _CallableList:
        return _CallableList([(k, _to_template_context(v)) for k, v in self._data.items()])

    def get(self, key: str, default: Any = None) -> Any:
        if key in self._data:
            return _to_template_context(self._data[key])
        return default

    def __getattr__(self, name: str) -> Any:
        if name in self._data:
            return _to_template_context(self._data[name])
        raise AttributeError(name)


def render_resume_to_docx(
    resume_json: Any,
    template_path: str,
    file_name: str = "resume.docx",
) -> RenderedDocxArtifact:
    """Render a resume JSON into DOCX using a template."""
    validated_resume = _normalize_resume_for_template(_validate_resume_json(resume_json))
    validated_template_path = _validate_template_path(template_path)
    _normalize_file_name(file_name)

    temp_dir = tempfile.TemporaryDirectory(prefix="widenet-resume-render-")
    work_dir = Path(temp_dir.name)
    docx_output = work_dir / "rendered_resume.docx"

    template_context = _to_template_context(validated_resume)

    try:
        template = DocxTemplate(str(validated_template_path))
        template.render(template_context)
        template.save(str(docx_output))
    except Exception as exc:
        temp_dir.cleanup()
        _logger.exception("Failed to render DOCX from template '%s'.", validated_template_path)
        raise ResumeRenderFailedError("Failed to render DOCX from template.") from exc

    if not docx_output.exists():
        temp_dir.cleanup()
        _logger.error("DOCX output file was not created at '%s'.", docx_output)
        raise ResumeRenderFailedError("DOCX output file was not created.")

    return RenderedDocxArtifact(docx_path=str(docx_output), temp_dir=temp_dir)


def _validate_resume_json(resume_json: Any) -> dict[str, Any]:
    if not isinstance(resume_json, dict):
        raise ResumeRenderValidationError("Field 'resume_json' must be a JSON object.")

    missing = sorted(_REQUIRED_FIELDS - set(resume_json.keys()))
    if missing:
        raise ResumeRenderValidationError(
            f"Field 'resume_json' is missing required keys: {', '.join(missing)}."
        )

    return resume_json


def _validate_template_path(template_path: str) -> Path:
    raw_path = Path(template_path).expanduser()
    project_root = Path(__file__).resolve().parents[2]

    # Resolve relative template paths from project root so runtime cwd does not matter.
    candidates: list[Path] = []
    if raw_path.is_absolute():
        candidates.append(raw_path)
    else:
        candidates.append(Path.cwd() / raw_path)
        candidates.append(project_root / raw_path)

        # Common project convention for templates under app/resume-templates.
        candidates.append(project_root / "app" / raw_path)

        # If caller passed only a filename, also search known template directories.
        if raw_path.parent == Path("."):
            candidates.append(project_root / "resume-templates" / raw_path.name)
            candidates.append(project_root / "app" / "resume-templates" / raw_path.name)

    resolved_path: Path | None = None
    for candidate in candidates:
        candidate_resolved = candidate.resolve()
        if candidate_resolved.is_file():
            resolved_path = candidate_resolved
            break

    if resolved_path is None:
        checked = ", ".join(str(c.resolve()) for c in candidates)
        _logger.error("Template not found. requested='%s' checked=[%s]", template_path, checked)
        raise ResumeRenderValidationError(
            f"Template file does not exist: '{template_path}'."
        )

    path = resolved_path
    if path.suffix.lower() != ".docx":
        raise ResumeRenderValidationError("Field 'template_path' must point to a .docx file.")
    return path


def _normalize_file_name(file_name: str | None) -> str:
    name = (file_name or "resume.docx").strip() or "resume.docx"
    if not name.lower().endswith(".docx"):
        name = f"{name}.docx"
    return name


def _to_template_context(value: Any) -> Any:
    if isinstance(value, dict):
        return _TemplateMapping(value)
    if isinstance(value, list):
        return [_to_template_context(item) for item in value]
    return value


def _normalize_resume_for_template(resume: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(resume)
    normalized["skills"] = _normalize_skills_structure(resume.get("skills"))
    return normalized


def _normalize_skills_structure(skills: Any) -> list[dict[str, Any]]:
    if isinstance(skills, list):
        normalized_list: list[dict[str, Any]] = []
        for entry in skills:
            if isinstance(entry, dict):
                category = str(entry.get("category", "")).strip()
                items_raw = entry.get("items", [])
                items = [str(item).strip() for item in (items_raw or []) if str(item).strip()]
                normalized_list.append({"category": category, "items": items})
                continue

            # Handle accidental tuple-pair shape like:
            # [('category', 'Languages'), ('items', ['Python'])]
            if isinstance(entry, (list, tuple)):
                try:
                    entry_dict = dict(entry)
                except (TypeError, ValueError):
                    continue
                category = str(entry_dict.get("category", "")).strip()
                items_raw = entry_dict.get("items", [])
                items = [str(item).strip() for item in (items_raw or []) if str(item).strip()]
                normalized_list.append({"category": category, "items": items})
        return normalized_list

    if isinstance(skills, dict):
        normalized_list = []
        for category, items_raw in skills.items():
            items = [str(item).strip() for item in (items_raw or []) if str(item).strip()]
            normalized_list.append({"category": str(category), "items": items})
        return normalized_list

    return []
