from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from .boltzio import load_manifest
from .report import collect_affinity_results


@dataclass(frozen=True)
class RunStatus:
    accepted_count: int
    completed_count: int
    remaining_count: int
    rejected_count: int
    completed_jobs: list[str]
    remaining_jobs: list[str]


def inspect_run(run_dir: str | Path) -> RunStatus:
    base = Path(run_dir)
    manifest = load_manifest(base / "manifest.json")
    jobs = manifest.get("jobs", [])
    completed = completed_job_ids(base)
    all_ids = [str(job["job_id"]) for job in jobs]
    remaining = [job_id for job_id in all_ids if job_id not in completed]
    return RunStatus(
        accepted_count=int(manifest.get("accepted_count", len(jobs))),
        completed_count=len(completed),
        remaining_count=len(remaining),
        rejected_count=int(manifest.get("rejected_count", 0)),
        completed_jobs=sorted(completed),
        remaining_jobs=remaining,
    )


def completed_job_ids(run_dir: str | Path) -> set[str]:
    return {result.job_id for result in collect_affinity_results(run_dir)}


def make_remaining_input_dir(run_dir: str | Path) -> Path:
    base = Path(run_dir)
    manifest = load_manifest(base / "manifest.json")
    completed = completed_job_ids(base)
    remaining_dir = base / "_remaining_inputs"
    if remaining_dir.exists():
        shutil.rmtree(remaining_dir)
    remaining_dir.mkdir(parents=True, exist_ok=True)

    copied = 0
    for job in manifest.get("jobs", []):
        job_id = str(job["job_id"])
        if job_id in completed:
            continue
        source = resolve_job_yaml(base, str(job["yaml_path"]))
        if not source.exists():
            raise FileNotFoundError(f"Could not find YAML for {job_id}: {source}")
        shutil.copy2(source, remaining_dir / source.name)
        copied += 1

    if copied == 0:
        raise RuntimeError("No remaining jobs to run.")
    return remaining_dir


def resolve_job_yaml(run_dir: Path, yaml_path: str) -> Path:
    raw = Path(yaml_path)
    if raw.is_absolute() or raw.exists():
        return raw
    candidate = run_dir / raw
    if candidate.exists():
        return candidate
    candidate = run_dir / "inputs" / raw.name
    if candidate.exists():
        return candidate
    return raw

