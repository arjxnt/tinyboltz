from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .fetch import fetch_uniprot_fasta


@dataclass(frozen=True)
class StarterPack:
    pack_id: str
    disease_area: str
    target_name: str
    uniprot_accession: str
    why_it_matters: str


STARTER_PACKS: dict[str, StarterPack] = {
    "tb-inha": StarterPack(
        pack_id="tb-inha",
        disease_area="tuberculosis",
        target_name="Mycobacterium tuberculosis InhA",
        uniprot_accession="P9WGR1",
        why_it_matters="InhA is a validated tuberculosis drug target connected to isoniazid biology.",
    ),
    "malaria-dhfr": StarterPack(
        pack_id="malaria-dhfr",
        disease_area="malaria",
        target_name="Plasmodium falciparum DHFR-TS",
        uniprot_accession="P13922",
        why_it_matters="DHFR-TS is a classic antimalarial target in folate metabolism.",
    ),
    "chagas-cruzain": StarterPack(
        pack_id="chagas-cruzain",
        disease_area="Chagas disease",
        target_name="Trypanosoma cruzi cruzain/cruzipain",
        uniprot_accession="P25779",
        why_it_matters="Cruzain/cruzipain is a cysteine protease target explored for Chagas therapeutics.",
    ),
}


STARTER_LIGANDS = [
    ("CC(=O)OC1=CC=CC=C1C(=O)O", "aspirin"),
    ("CC(C)CC1=CC=C(C=C1)C(C)C(=O)O", "ibuprofen"),
    ("CC(=O)NC1=CC=C(O)C=C1", "acetaminophen"),
    ("CN(C)C(=N)NC(=N)N", "metformin"),
    ("C1=CC=C(C=C1)C(CN)O", "phenylethanolamine"),
    ("CCN(CC)CCCC(C)NC1=C2C=CC(=CC2=NC=C1)Cl", "chloroquine"),
    ("CC1=C(C(=NO1)C)S(=O)(=O)N", "sulfamethoxazole_core"),
    ("CN1C=NC2=C1C(=O)N(C(=O)N2C)C", "caffeine"),
]


def write_starter_pack(pack_id: str, output_dir: str | Path, fetch_target: bool = True) -> dict:
    if pack_id not in STARTER_PACKS:
        choices = ", ".join(sorted(STARTER_PACKS))
        raise ValueError(f"Unknown starter pack '{pack_id}'. Choices: {choices}")

    pack = STARTER_PACKS[pack_id]
    base = Path(output_dir)
    target_dir = base / "targets"
    ligand_dir = base / "ligands"
    target_dir.mkdir(parents=True, exist_ok=True)
    ligand_dir.mkdir(parents=True, exist_ok=True)

    fasta_path = target_dir / f"{pack_id}.fasta"
    if fetch_target:
        fetch_uniprot_fasta(pack.uniprot_accession, fasta_path)
    else:
        fasta_path.write_text(
            f">{pack.uniprot_accession} {pack.target_name} fetch with: tinyboltz fetch-target --uniprot {pack.uniprot_accession}\n",
            encoding="utf-8",
        )

    ligands_path = ligand_dir / "starter_ligands.smi"
    ligands_path.write_text(
        "\n".join(f"{smiles} {name}" for smiles, name in STARTER_LIGANDS) + "\n",
        encoding="utf-8",
    )

    metadata = {
        "pack": asdict(pack),
        "target_fasta": str(fasta_path),
        "ligands": str(ligands_path),
        "note": "Starter ligands are workflow seeds and sanity checks, not medical recommendations.",
    }
    (base / "pack.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata
