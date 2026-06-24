from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .boltzio import load_manifest
from .status import resolve_job_yaml


@dataclass(frozen=True)
class ValidationIssue:
    level: str
    message: str


def validate_run(run_dir: str | Path) -> list[ValidationIssue]:
    base = Path(run_dir)
    issues: list[ValidationIssue] = []
    manifest_path = base / "manifest.json"
    if not manifest_path.exists():
        return [ValidationIssue("error", f"Missing manifest: {manifest_path}")]

    try:
        manifest = load_manifest(manifest_path)
    except Exception as exc:
        return [ValidationIssue("error", f"Could not read manifest: {exc}")]

    jobs = manifest.get("jobs", [])
    if not isinstance(jobs, list):
        return [ValidationIssue("error", "Manifest field 'jobs' must be a list")]
    accepted_count = _int_or_none(manifest.get("accepted_count", len(jobs)))
    if accepted_count is None:
        issues.append(ValidationIssue("error", "accepted_count must be an integer"))
    elif accepted_count != len(jobs):
        issues.append(ValidationIssue("warn", "accepted_count does not match number of jobs"))

    seen: set[str] = set()
    for index, job in enumerate(jobs, start=1):
        if not isinstance(job, dict):
            issues.append(ValidationIssue("error", f"Job {index} is not an object"))
            continue
        job_id = str(job.get("job_id", ""))
        yaml_path = str(job.get("yaml_path", ""))
        if not job_id:
            issues.append(ValidationIssue("error", f"Job {index} is missing job_id"))
        elif job_id in seen:
            issues.append(ValidationIssue("error", f"Duplicate job_id: {job_id}"))
        else:
            seen.add(job_id)
        if not yaml_path:
            issues.append(ValidationIssue("error", f"Job {job_id or index} is missing yaml_path"))
            continue
        if not resolve_job_yaml(base, yaml_path).exists():
            issues.append(ValidationIssue("error", f"Missing YAML for {job_id}: {yaml_path}"))

    if not issues:
        issues.append(ValidationIssue("ok", "Run manifest and YAML inputs look consistent"))
    return issues


def format_validation(issues: list[ValidationIssue]) -> str:
    width = max(len(issue.level) for issue in issues)
    return "\n".join(f"{issue.level.upper():<{width}}  {issue.message}" for issue in issues)


def has_errors(issues: list[ValidationIssue]) -> bool:
    return any(issue.level == "error" for issue in issues)


def _int_or_none(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
