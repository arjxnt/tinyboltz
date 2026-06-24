from pathlib import Path

from tinyboltz.boltzio import prepare_jobs
from tinyboltz.fasta import ProteinTarget
from tinyboltz.ligands import Ligand, LigandFilterConfig, filter_ligands
from tinyboltz.runner import build_boltz_command
from tinyboltz.status import inspect_run
from tinyboltz.validate import has_errors, validate_run


def test_filter_rejects_metals_and_duplicates():
    ligands = [
        Ligand("L0001", "CCO", "ethanol", 1),
        Ligand("L0002", "CCO", "ethanol_copy", 2),
        Ligand("L0003", "[Fe]C", "iron", 3),
    ]
    accepted, rejected = filter_ligands(ligands, LigandFilterConfig())
    assert [ligand.ligand_id for ligand in accepted] == ["L0001"]
    assert [item.reason for item in rejected] == ["duplicate_smiles", "metal_containing_smiles"]


def test_prepare_writes_boltz_yaml(tmp_path: Path):
    target = ProteinTarget("T", "MSEQNNTEMT")
    ligand = Ligand("L0001", "CCO", "ethanol", 1)
    jobs = prepare_jobs(target, [ligand], tmp_path)
    assert len(jobs) == 1
    yaml_text = Path(jobs[0].yaml_path).read_text(encoding="utf-8")
    assert "sequences:" in yaml_text
    assert 'smiles: "CCO"' in yaml_text
    assert "properties:" in yaml_text
    assert "affinity:" in yaml_text


def test_build_boltz_command_dry_run_shape():
    command = build_boltz_command("inputs", "out", use_msa_server=True, accelerator="gpu")
    assert command.args[:3] == ["boltz", "predict", "inputs"]
    assert "--use_msa_server" in command.args
    assert "--accelerator" in command.args


def test_status_counts_remaining_jobs(tmp_path: Path):
    target = ProteinTarget("T", "MSEQNNTEMT")
    ligand = Ligand("L0001", "CCO", "ethanol", 1)
    jobs = prepare_jobs(target, [ligand], tmp_path)
    from tinyboltz.boltzio import write_manifest

    write_manifest(tmp_path / "manifest.json", target, jobs, source_ligands="x.smi", rejected_count=0)
    status = inspect_run(tmp_path)
    assert status.accepted_count == 1
    assert status.completed_count == 0
    assert status.remaining_jobs == ["L0001_ethanol"]


def test_validate_run_accepts_prepared_manifest(tmp_path: Path):
    target = ProteinTarget("T", "MSEQNNTEMT")
    ligand = Ligand("L0001", "CCO", "ethanol", 1)
    jobs = prepare_jobs(target, [ligand], tmp_path)
    from tinyboltz.boltzio import write_manifest

    write_manifest(tmp_path / "manifest.json", target, jobs, source_ligands="x.smi", rejected_count=0)
    assert not has_errors(validate_run(tmp_path))
