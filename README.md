# TinyBoltz

Make frontier protein-ligand AI usable by a tiny lab with one GPU and no pharma budget.

![status](https://img.shields.io/badge/status-research%20prototype-087f8c)
![license](https://img.shields.io/badge/license-MIT-29464e)
![compute](https://img.shields.io/badge/compute-explicit%20--execute-9a5b00)
![model](https://img.shields.io/badge/model-Boltz--2-0f5f6b)

TinyBoltz is a lightweight command-line workflow around Boltz-2. It turns a protein target and a ligand library into resumable Boltz YAML jobs, keeps cheap filtering ahead of GPU inference, and produces a shareable HTML report from affinity outputs.

This repository does not vendor Boltz-2. It prepares and runs jobs for the Hugging Face-facing Boltz-2 ecosystem, especially `boltz-community/boltz-2`, through the upstream `boltz predict` command.

## What It Does

- Reads a FASTA protein target.
- Reads ligands from `.smi`, `.smiles`, or `.csv`.
- Filters invalid or expensive-looking molecules before GPU use.
- Writes one Boltz YAML complex per ligand.
- Creates a manifest for reproducibility and resume logic.
- Optionally downloads/caches a Hugging Face model snapshot.
- Runs Boltz only when explicitly asked with `--execute`.
- Builds an HTML report from Boltz affinity JSON outputs.
- Fetches public protein targets from UniProt.
- Creates starter packs for neglected-disease workflows.
- Resumes interrupted runs with `--remaining-only`.
- Checks local readiness with `doctor`.
- Estimates GPU-hours before a run with `budget`.
- Validates prepared manifests before execution.
- Exports ranked results as HTML, CSV, and JSON.
- Writes markdown runbooks for small-lab handoff.

## Command Surface

| Command | What it does |
| --- | --- |
| `screen` | Prepare, optionally execute, and report in one command. |
| `prepare` | Build Boltz YAML jobs and a manifest. |
| `run` | Dry-run or execute Boltz. |
| `status` | Show completed and remaining jobs. |
| `validate` | Check manifest/YAML consistency before GPU use. |
| `budget` | Estimate GPU hours before running. |
| `plan` | Write a markdown execution runbook. |
| `report` | Build an HTML evidence dashboard. |
| `fetch-target` | Download a UniProt FASTA target. |
| `init-pack` | Create a neglected-disease starter pack. |
| `doctor` | Check environment readiness. |
| `cache-model` | Cache Hugging Face model snapshots. |

## Install

From this folder:

```bash
python -m pip install -e .
```

Optional extras:

```bash
python -m pip install -e ".[chem,hf,dev]"
```

For actual Boltz inference, install Boltz in the same environment according to the upstream docs:

```bash
python -m pip install "boltz[cuda]" -U
```

## Quick Start Without A GPU

Do the whole dry-run workflow in one command:

```bash
tinyboltz screen \
  --target examples/targets/demo_target.fasta \
  --ligands examples/ligands/demo_ligands.smi \
  --out runs/demo \
  --limit 5
```

Or run each step yourself.

Prepare example jobs:

```bash
tinyboltz prepare \
  --target examples/targets/demo_target.fasta \
  --ligands examples/ligands/demo_ligands.smi \
  --out runs/demo \
  --limit 5
```

Preview the Boltz command:

```bash
tinyboltz run --prepared runs/demo
```

Create a report from any available prediction JSON files:

```bash
tinyboltz report \
  --run runs/demo \
  --out runs/demo/report.html \
  --csv runs/demo/results.csv \
  --json runs/demo/results.json
```

Use an operational profile:

```bash
tinyboltz screen \
  --profile configs/profiles/tiny-gpu.yaml \
  --target examples/targets/demo_target.fasta \
  --ligands examples/ligands/demo_ligands.smi \
  --out runs/profile-demo
```

## Run Boltz For Real

This is the first command that can spend meaningful GPU time:

```bash
tinyboltz run \
  --prepared runs/demo \
  --execute \
  --use-potentials \
  --accelerator gpu
```

Resume only jobs that do not already have affinity JSON outputs:

```bash
tinyboltz run --prepared runs/demo --remaining-only --execute --accelerator gpu
```

Check progress:

```bash
tinyboltz status --run runs/demo
```

Validate the prepared run:

```bash
tinyboltz validate --run runs/demo
```

Estimate cost before running:

```bash
tinyboltz budget --run runs/demo --minutes-per-job 8 --batch-size 1
```

Write an execution runbook:

```bash
tinyboltz plan --run runs/demo --out runs/demo/RUNBOOK.md
```

Check the local environment:

```bash
tinyboltz doctor
```

## Starter Packs

Create a tiny neglected-disease pack with a public UniProt target and starter ligands:

```bash
tinyboltz init-pack --pack tb-inha --out packs/tb-inha
```

Available packs:

- `tb-inha`: Mycobacterium tuberculosis InhA.
- `malaria-dhfr`: Plasmodium falciparum DHFR-TS.
- `chagas-cruzain`: Trypanosoma cruzi cruzain/cruzipain.

Then screen it:

```bash
tinyboltz screen \
  --target packs/tb-inha/targets/tb-inha.fasta \
  --ligands packs/tb-inha/ligands/starter_ligands.smi \
  --out runs/tb-inha \
  --limit 8
```

Fetch any UniProt target directly:

```bash
tinyboltz fetch-target --uniprot P9WGR1 --out targets/tb-inha.fasta
```

## Hugging Face Cache Helper

If `huggingface_hub` is installed:

```bash
tinyboltz cache-model --repo-id boltz-community/boltz-2
```

## Output Layout

```text
runs/demo/
  inputs/
    L0001_aspirin.yaml
    L0002_caffeine.yaml
  manifest.json
  rejected.csv
  report.html
  _remaining_inputs/
```

Boltz itself may write predictions into its own output directory. TinyBoltz searches below the run directory for affinity JSON files and associated `.cif`/`.pdb` structures when making reports.

## Safety And Interpretation

TinyBoltz results are prioritization signals, not medical claims. Boltz affinity estimates need calibration and experimental validation before anyone treats a molecule as a hit. The tool is designed to conserve scarce compute and produce reproducible evidence bundles for researchers.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The best contributions improve tiny-lab usefulness: better target packs, better low-cost ligand filtering, benchmark calibration, pose visualization, and hard budget controls.

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/ROADMAP.md](docs/ROADMAP.md).

GitHub Actions CI is included as [docs/GITHUB_ACTIONS_CI.yml](docs/GITHUB_ACTIONS_CI.yml). Copy it to `.github/workflows/ci.yml` from a token/session with GitHub `workflow` scope to enable Actions.

## Why This Exists

The goal is not to train a new foundation model. The goal is to make an open, frontier protein-ligand model practical for small labs: neglected disease teams, student groups, rare disease researchers, and anyone who has a target but not a pharma compute budget.
