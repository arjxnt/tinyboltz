from __future__ import annotations

import importlib.util
import platform
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str


def run_checks(project_root: str | Path | None = None) -> list[Check]:
    root = Path(project_root) if project_root else Path.cwd()
    return [
        Check("python", "ok", f"{sys.version.split()[0]} on {platform.system()}"),
        _module_check("huggingface_hub", "optional HF model snapshot caching"),
        _module_check("rdkit", "optional chemistry-grade ligand validation"),
        _binary_check("boltz", "required only for --execute GPU inference"),
        _path_check(root / "examples" / "targets" / "demo_target.fasta", "example target FASTA"),
        _path_check(root / "examples" / "ligands" / "demo_ligands.smi", "example ligand library"),
    ]


def format_checks(checks: list[Check]) -> str:
    width = max(len(check.name) for check in checks)
    lines = []
    for check in checks:
        mark = {"ok": "OK", "missing": "MISS", "warn": "WARN"}.get(check.status, check.status.upper())
        lines.append(f"{mark:>4}  {check.name:<{width}}  {check.detail}")
    return "\n".join(lines)


def _module_check(module_name: str, purpose: str) -> Check:
    if importlib.util.find_spec(module_name):
        return Check(module_name, "ok", purpose)
    return Check(module_name, "missing", purpose)


def _binary_check(binary: str, purpose: str) -> Check:
    path = shutil.which(binary)
    if path:
        return Check(binary, "ok", path)
    return Check(binary, "missing", purpose)


def _path_check(path: Path, purpose: str) -> Check:
    if path.exists():
        return Check(path.name, "ok", str(path))
    return Check(path.name, "missing", purpose)

