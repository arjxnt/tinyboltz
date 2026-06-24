from __future__ import annotations

import argparse
from pathlib import Path

from .boltzio import prepare_jobs, write_manifest
from .budget import estimate_budget, format_budget
from .diagnostics import format_checks, run_checks
from .fasta import read_first_fasta
from .fetch import fetch_uniprot_fasta
from .hf import cache_model
from .ligands import LigandFilterConfig, RejectedLigand, filter_ligands, load_ligands, write_rejections
from .packs import STARTER_PACKS, write_starter_pack
from .report import write_html_report
from .runner import build_boltz_command, run_boltz
from .status import inspect_run, make_remaining_input_dir


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tinyboltz",
        description="One-GPU Boltz-2 screening workflow for tiny labs.",
    )
    subparsers = parser.add_subparsers(required=True)

    prepare = subparsers.add_parser("prepare", help="Prepare Boltz YAML jobs from a target and ligands.")
    prepare.add_argument("--target", required=True, help="Protein FASTA file.")
    prepare.add_argument("--ligands", required=True, help="Ligand .smi/.smiles/.csv file.")
    prepare.add_argument("--out", required=True, help="Output run directory.")
    prepare.add_argument("--limit", type=int, default=None, help="Maximum accepted ligands to write.")
    prepare.add_argument("--max-smiles-len", type=int, default=220)
    prepare.add_argument("--max-heavy-atoms", type=int, default=80)
    prepare.add_argument("--allow-metals", action="store_true")
    prepare.add_argument("--protein-chain-id", default="A")
    prepare.add_argument("--ligand-chain-id", default="B")
    prepare.set_defaults(func=cmd_prepare)

    run = subparsers.add_parser("run", help="Preview or execute Boltz on a prepared run.")
    run.add_argument("--prepared", required=True, help="Prepared TinyBoltz run directory.")
    run.add_argument("--execute", action="store_true", help="Actually run Boltz. Omit for dry-run.")
    run.add_argument("--no-msa-server", action="store_true", help="Do not pass --use_msa_server.")
    run.add_argument("--use-potentials", action="store_true")
    run.add_argument("--accelerator", default=None, help="Optional Boltz accelerator, e.g. gpu or cpu.")
    run.add_argument("--model", default="boltz2", help="Optional Boltz model argument.")
    run.add_argument("--override", action="store_true")
    run.add_argument("--boltz-out", default=None, help="Optional Boltz output directory.")
    run.add_argument("--remaining-only", action="store_true", help="Run only jobs without affinity JSON outputs.")
    run.set_defaults(func=cmd_run)

    screen = subparsers.add_parser("screen", help="Prepare, optionally run, and report in one command.")
    screen.add_argument("--target", required=True, help="Protein FASTA file.")
    screen.add_argument("--ligands", required=True, help="Ligand .smi/.smiles/.csv file.")
    screen.add_argument("--out", required=True, help="Output run directory.")
    screen.add_argument("--limit", type=int, default=None)
    screen.add_argument("--max-smiles-len", type=int, default=220)
    screen.add_argument("--max-heavy-atoms", type=int, default=80)
    screen.add_argument("--allow-metals", action="store_true")
    screen.add_argument("--protein-chain-id", default="A")
    screen.add_argument("--ligand-chain-id", default="B")
    screen.add_argument("--execute", action="store_true", help="Actually run Boltz. Omit for dry-run.")
    screen.add_argument("--no-msa-server", action="store_true")
    screen.add_argument("--use-potentials", action="store_true")
    screen.add_argument("--accelerator", default=None)
    screen.add_argument("--model", default="boltz2")
    screen.add_argument("--override", action="store_true")
    screen.add_argument("--boltz-out", default=None)
    screen.add_argument("--report-out", default=None)
    screen.set_defaults(func=cmd_screen)

    status = subparsers.add_parser("status", help="Show completed and remaining jobs for a run.")
    status.add_argument("--run", required=True, help="TinyBoltz run directory.")
    status.set_defaults(func=cmd_status)

    budget = subparsers.add_parser("budget", help="Estimate GPU hours before running a screen.")
    budget.add_argument("--run", help="TinyBoltz run directory.")
    budget.add_argument("--jobs", type=int, help="Number of jobs if no run directory is available.")
    budget.add_argument("--completed", type=int, default=0)
    budget.add_argument("--minutes-per-job", type=float, default=8.0)
    budget.add_argument("--batch-size", type=int, default=1)
    budget.set_defaults(func=cmd_budget)

    doctor = subparsers.add_parser("doctor", help="Check local readiness for TinyBoltz and Boltz.")
    doctor.add_argument("--project-root", default=".")
    doctor.set_defaults(func=cmd_doctor)

    report = subparsers.add_parser("report", help="Create an HTML report from Boltz affinity outputs.")
    report.add_argument("--run", required=True, help="TinyBoltz run directory.")
    report.add_argument("--out", required=True, help="Report HTML path.")
    report.set_defaults(func=cmd_report)

    fetch_target = subparsers.add_parser("fetch-target", help="Fetch a target FASTA from UniProt.")
    fetch_target.add_argument("--uniprot", required=True, help="UniProt accession.")
    fetch_target.add_argument("--out", required=True, help="Output FASTA path.")
    fetch_target.set_defaults(func=cmd_fetch_target)

    init_pack = subparsers.add_parser("init-pack", help="Create a neglected-disease starter pack.")
    init_pack.add_argument("--pack", required=True, choices=sorted(STARTER_PACKS))
    init_pack.add_argument("--out", required=True, help="Output pack directory.")
    init_pack.add_argument("--no-fetch", action="store_true", help="Do not contact UniProt; write a placeholder target.")
    init_pack.set_defaults(func=cmd_init_pack)

    cache = subparsers.add_parser("cache-model", help="Cache a Hugging Face model snapshot.")
    cache.add_argument("--repo-id", default="boltz-community/boltz-2")
    cache.add_argument("--revision", default=None)
    cache.add_argument("--cache-dir", default=None)
    cache.set_defaults(func=cmd_cache_model)

    return parser


def cmd_prepare(args: argparse.Namespace) -> int:
    out, jobs, rejected = prepare_from_args(args)
    print(f"Prepared {len(jobs)} Boltz jobs in {out / 'inputs'}")
    print(f"Rejected {len(rejected)} ligands; details: {out / 'rejected.csv'}")
    return 0


def prepare_from_args(args: argparse.Namespace):
    target = read_first_fasta(args.target)
    ligands = load_ligands(args.ligands)
    config = LigandFilterConfig(
        max_smiles_len=args.max_smiles_len,
        max_heavy_atoms=args.max_heavy_atoms,
        allow_metals=args.allow_metals,
    )
    accepted, rejected = filter_ligands(ligands, config)
    if args.limit is not None:
        overflow = accepted[args.limit :]
        accepted = accepted[: args.limit]
        rejected.extend(
            [
                RejectedLigand(
                    source_index=ligand.source_index,
                    smiles=ligand.smiles,
                    name=ligand.name,
                    reason="over_limit",
                )
                for ligand in overflow
            ]
        )

    out = Path(args.out)
    jobs = prepare_jobs(
        target=target,
        ligands=accepted,
        output_dir=out,
        protein_chain_id=args.protein_chain_id,
        ligand_chain_id=args.ligand_chain_id,
    )
    write_manifest(
        out / "manifest.json",
        target,
        jobs,
        source_ligands=str(Path(args.ligands)),
        rejected_count=len(rejected),
    )
    write_rejections(out / "rejected.csv", rejected)
    return out, jobs, rejected


def cmd_run(args: argparse.Namespace) -> int:
    return run_prepared(
        prepared=Path(args.prepared),
        execute=args.execute,
        no_msa_server=args.no_msa_server,
        use_potentials=args.use_potentials,
        accelerator=args.accelerator,
        model=args.model,
        override=args.override,
        boltz_out=Path(args.boltz_out) if args.boltz_out else None,
        remaining_only=args.remaining_only,
    )


def run_prepared(
    *,
    prepared: Path,
    execute: bool,
    no_msa_server: bool,
    use_potentials: bool,
    accelerator: str | None,
    model: str | None,
    override: bool,
    boltz_out: Path | None,
    remaining_only: bool = False,
) -> int:
    prepared = Path(prepared)
    input_dir = prepared / "inputs"
    if not input_dir.exists():
        raise SystemExit(f"No inputs directory found at {input_dir}")
    if remaining_only:
        input_dir = make_remaining_input_dir(prepared)
    boltz_out = boltz_out if boltz_out else prepared / "boltz_output"
    command = build_boltz_command(
        input_path=input_dir,
        output_dir=boltz_out,
        use_msa_server=not no_msa_server,
        use_potentials=use_potentials,
        accelerator=accelerator,
        model=model,
        override=override,
    )
    if not execute:
        print("Dry run. Add --execute to spend compute.")
        print(command.shell_text())
        return 0
    return run_boltz(command)


def cmd_screen(args: argparse.Namespace) -> int:
    out, jobs, rejected = prepare_from_args(args)
    print(f"Prepared {len(jobs)} Boltz jobs in {out / 'inputs'}")
    print(f"Rejected {len(rejected)} ligands; details: {out / 'rejected.csv'}")
    exit_code = run_prepared(
        prepared=out,
        execute=args.execute,
        no_msa_server=args.no_msa_server,
        use_potentials=args.use_potentials,
        accelerator=args.accelerator,
        model=args.model,
        override=args.override,
        boltz_out=Path(args.boltz_out) if args.boltz_out else None,
        remaining_only=False,
    )
    report_out = Path(args.report_out) if args.report_out else out / "report.html"
    write_html_report(out, report_out)
    print(f"Wrote report to {report_out}")
    return exit_code


def cmd_status(args: argparse.Namespace) -> int:
    status = inspect_run(args.run)
    print(f"Accepted:  {status.accepted_count}")
    print(f"Completed: {status.completed_count}")
    print(f"Remaining: {status.remaining_count}")
    print(f"Rejected:  {status.rejected_count}")
    if status.remaining_jobs:
        preview = ", ".join(status.remaining_jobs[:10])
        suffix = " ..." if len(status.remaining_jobs) > 10 else ""
        print(f"Next remaining: {preview}{suffix}")
    return 0


def cmd_budget(args: argparse.Namespace) -> int:
    if args.run:
        status = inspect_run(args.run)
        jobs = status.accepted_count
        completed = status.completed_count
    elif args.jobs is not None:
        jobs = args.jobs
        completed = args.completed
    else:
        raise SystemExit("Provide --run or --jobs.")
    plan = estimate_budget(
        jobs=jobs,
        completed=completed,
        minutes_per_job=args.minutes_per_job,
        batch_size=args.batch_size,
    )
    print(format_budget(plan))
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    checks = run_checks(args.project_root)
    print(format_checks(checks))
    missing_required = [check for check in checks if check.name == "boltz" and check.status == "missing"]
    return 2 if missing_required else 0


def cmd_report(args: argparse.Namespace) -> int:
    write_html_report(args.run, args.out)
    print(f"Wrote report to {args.out}")
    return 0


def cmd_fetch_target(args: argparse.Namespace) -> int:
    output = fetch_uniprot_fasta(args.uniprot, args.out)
    print(f"Wrote FASTA to {output}")
    return 0


def cmd_init_pack(args: argparse.Namespace) -> int:
    metadata = write_starter_pack(args.pack, args.out, fetch_target=not args.no_fetch)
    print(f"Wrote starter pack to {args.out}")
    print(f"Target:  {metadata['target_fasta']}")
    print(f"Ligands: {metadata['ligands']}")
    return 0


def cmd_cache_model(args: argparse.Namespace) -> int:
    path = cache_model(repo_id=args.repo_id, revision=args.revision, cache_dir=args.cache_dir)
    print(path)
    return 0
