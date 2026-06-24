from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .fasta import ProteinTarget
from .ligands import Ligand


@dataclass(frozen=True)
class PreparedJob:
    job_id: str
    ligand_id: str
    ligand_name: str
    smiles: str
    yaml_path: str


def prepare_jobs(
    target: ProteinTarget,
    ligands: list[Ligand],
    output_dir: str | Path,
    protein_chain_id: str = "A",
    ligand_chain_id: str = "B",
) -> list[PreparedJob]:
    base = Path(output_dir)
    input_dir = base / "inputs"
    input_dir.mkdir(parents=True, exist_ok=True)
    jobs: list[PreparedJob] = []

    for ligand in ligands:
        job_id = f"{ligand.ligand_id}_{ligand.name}"
        yaml_path = input_dir / f"{job_id}.yaml"
        yaml_path.write_text(
            render_boltz_yaml(
                target=target,
                ligand=ligand,
                protein_chain_id=protein_chain_id,
                ligand_chain_id=ligand_chain_id,
            ),
            encoding="utf-8",
        )
        jobs.append(
            PreparedJob(
                job_id=job_id,
                ligand_id=ligand.ligand_id,
                ligand_name=ligand.name,
                smiles=ligand.smiles,
                yaml_path=str(yaml_path),
            )
        )

    return jobs


def render_boltz_yaml(
    target: ProteinTarget,
    ligand: Ligand,
    protein_chain_id: str = "A",
    ligand_chain_id: str = "B",
) -> str:
    return "\n".join(
        [
            "version: 1",
            "sequences:",
            "  - protein:",
            f"      id: {quote_yaml(protein_chain_id)}",
            f"      sequence: {quote_yaml(target.sequence)}",
            "  - ligand:",
            f"      id: {quote_yaml(ligand_chain_id)}",
            f"      smiles: {quote_yaml(ligand.smiles)}",
            "properties:",
            "  - affinity:",
            f"      binder: {quote_yaml(ligand_chain_id)}",
            "",
        ]
    )


def write_manifest(
    path: str | Path,
    target: ProteinTarget,
    jobs: list[PreparedJob],
    *,
    source_ligands: str,
    rejected_count: int,
) -> None:
    manifest = {
        "tool": "tinyboltz",
        "schema_version": 1,
        "target": asdict(target),
        "source_ligands": source_ligands,
        "accepted_count": len(jobs),
        "rejected_count": rejected_count,
        "jobs": [asdict(job) for job in jobs],
    }
    manifest_path = Path(path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def load_manifest(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def quote_yaml(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'

