# TinyBoltz Spec

North star: make frontier protein-ligand AI usable by a tiny lab with one GPU and no pharma budget.

## MVP

- [x] Read one protein target from FASTA.
- [x] Read ligands from `.smi`, `.smiles`, or `.csv`.
- [x] Reject obvious bad or expensive ligands before GPU inference.
- [x] Generate one Boltz affinity YAML per accepted ligand.
- [x] Write a reproducible `manifest.json`.
- [x] Preview the exact `boltz predict` command.
- [x] Require `--execute` before spending GPU time.
- [x] Generate an HTML report from affinity JSON outputs.
- [x] Optionally cache a Hugging Face model snapshot.
- [x] Fetch targets from UniProt.
- [x] Initialize neglected-disease starter packs.
- [x] Show run status and remaining jobs.
- [x] Run only remaining jobs after an interrupted run.
- [x] Provide a one-command `screen` workflow.
- [x] Link structure files in the report when Boltz outputs them.
- [x] Provide local diagnostics with `doctor`.
- [x] Estimate GPU-hour budgets with `budget`.
- [x] Include architecture and roadmap docs.
- [x] Include operational profiles for different compute situations.

## Next High-Impact Tasks

- [ ] Add calibration plots against public protein-ligand benchmark complexes.
- [ ] Add a purchasable-compound downloader with vendor-neutral source metadata.
- [ ] Add embedded 3Dmol.js rendering for top poses.
- [ ] Add GitHub Actions CI with no-GPU smoke tests.
