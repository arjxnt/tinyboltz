# Contributing To TinyBoltz

TinyBoltz is for practical open drug-discovery workflows on scarce compute. The highest-value contributions are the ones that help a small lab run a better screen, spend fewer GPU hours, or interpret results more honestly.

## Good First Contributions

- Add a public target starter pack with a UniProt accession and a short rationale.
- Improve ligand filters without adding heavy required dependencies.
- Add example runs that do not require a GPU.
- Improve error messages around Boltz install, missing outputs, and invalid SMILES.
- Add parsers for more Boltz output fields.

## High-Impact Contributions

- Benchmark calibration against public protein-ligand complexes.
- Vendor-neutral purchasable compound library downloaders.
- 3Dmol.js pose visualization for top structures.
- Resume logic that detects partial Boltz output states more precisely.
- Cloud profiles for one cheap GPU session with hard budget limits.
- Better environment checks for CUDA, GPU memory, disk space, and Boltz versions.
- New report exports for medicinal chemistry review packets.

## Ground Rules

- Do not claim predictions are therapies or validated hits.
- Keep GPU work behind explicit user action.
- Prefer small, testable changes.
- Keep core functionality usable with the Python standard library.
- Optional chemistry and Hugging Face dependencies should remain optional.
