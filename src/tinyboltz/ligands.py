from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path


SMILES_ALLOWED = re.compile(r"^[A-Za-z0-9@+\-\[\]\(\)\\/#=.$:%]+$")
METAL_TOKENS = {
    "Fe",
    "Zn",
    "Mg",
    "Mn",
    "Cu",
    "Co",
    "Ni",
    "Ca",
    "Na",
    "K",
    "Li",
    "Al",
    "Hg",
    "Pb",
    "Cd",
}


@dataclass(frozen=True)
class Ligand:
    ligand_id: str
    smiles: str
    name: str
    source_index: int


@dataclass(frozen=True)
class RejectedLigand:
    source_index: int
    smiles: str
    name: str
    reason: str


@dataclass(frozen=True)
class LigandFilterConfig:
    max_smiles_len: int = 220
    max_heavy_atoms: int = 80
    allow_metals: bool = False


def load_ligands(path: str | Path) -> list[Ligand]:
    ligand_path = Path(path)
    suffix = ligand_path.suffix.lower()
    if suffix in {".smi", ".smiles", ".txt"}:
        return _load_smi(ligand_path)
    if suffix == ".csv":
        return _load_csv(ligand_path)
    raise ValueError(f"Unsupported ligand file extension: {ligand_path.suffix}")


def filter_ligands(
    ligands: list[Ligand],
    config: LigandFilterConfig,
) -> tuple[list[Ligand], list[RejectedLigand]]:
    accepted: list[Ligand] = []
    rejected: list[RejectedLigand] = []
    seen: set[str] = set()

    for ligand in ligands:
        reason = rejection_reason(ligand.smiles, config)
        if not reason and ligand.smiles in seen:
            reason = "duplicate_smiles"
        if reason:
            rejected.append(
                RejectedLigand(
                    source_index=ligand.source_index,
                    smiles=ligand.smiles,
                    name=ligand.name,
                    reason=reason,
                )
            )
            continue
        seen.add(ligand.smiles)
        accepted.append(ligand)

    return accepted, rejected


def rejection_reason(smiles: str, config: LigandFilterConfig) -> str | None:
    if not smiles:
        return "empty_smiles"
    if len(smiles) > config.max_smiles_len:
        return "smiles_too_long"
    if not SMILES_ALLOWED.match(smiles):
        return "unsupported_smiles_characters"
    if not _balanced(smiles, "(", ")"):
        return "unbalanced_parentheses"
    if smiles.count("[") != smiles.count("]"):
        return "unbalanced_brackets"
    if not config.allow_metals and _contains_metal(smiles):
        return "metal_containing_smiles"

    rdkit_reason = _rdkit_rejection_reason(smiles, config)
    if rdkit_reason:
        return rdkit_reason

    if _rough_heavy_atom_count(smiles) > config.max_heavy_atoms:
        return "too_many_rough_heavy_atoms"
    return None


def write_rejections(path: str | Path, rejected: list[RejectedLigand]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["source_index", "name", "smiles", "reason"])
        writer.writeheader()
        for item in rejected:
            writer.writerow(
                {
                    "source_index": item.source_index,
                    "name": item.name,
                    "smiles": item.smiles,
                    "reason": item.reason,
                }
            )


def _load_smi(path: Path) -> list[Ligand]:
    ligands: list[Ligand] = []
    for index, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        smiles = parts[0]
        name = " ".join(parts[1:]) if len(parts) > 1 else f"ligand_{index}"
        ligands.append(
            Ligand(
                ligand_id=f"L{len(ligands) + 1:04d}",
                smiles=smiles,
                name=safe_name(name),
                source_index=index,
            )
        )
    return ligands


def _load_csv(path: Path) -> list[Ligand]:
    ligands: list[Ligand] = []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return ligands
        smiles_field = _pick_field(reader.fieldnames, ["smiles", "SMILES", "canonical_smiles"])
        name_field = _pick_field(reader.fieldnames, ["name", "Name", "compound", "compound_name", "id"])
        if not smiles_field:
            raise ValueError("CSV ligand file must include a smiles column")
        for index, row in enumerate(reader, start=2):
            smiles = (row.get(smiles_field) or "").strip()
            name = (row.get(name_field) or f"ligand_{index}").strip() if name_field else f"ligand_{index}"
            ligands.append(
                Ligand(
                    ligand_id=f"L{len(ligands) + 1:04d}",
                    smiles=smiles,
                    name=safe_name(name),
                    source_index=index,
                )
            )
    return ligands


def _pick_field(fields: list[str], candidates: list[str]) -> str | None:
    lowered = {field.lower(): field for field in fields}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    return None


def _balanced(value: str, left: str, right: str) -> bool:
    depth = 0
    for char in value:
        if char == left:
            depth += 1
        elif char == right:
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def _contains_metal(smiles: str) -> bool:
    bracket_tokens = re.findall(r"\[([A-Z][a-z]?)", smiles)
    return any(token in METAL_TOKENS for token in bracket_tokens)


def _rough_heavy_atom_count(smiles: str) -> int:
    bracket_atoms = re.findall(r"\[([A-Z][a-z]?|[cnopsb])", smiles)
    unbracketed = re.findall(r"Cl|Br|[BCNOFPSI]|[cnops]", re.sub(r"\[[^\]]+\]", "", smiles))
    return len(bracket_atoms) + len(unbracketed)


def _rdkit_rejection_reason(smiles: str, config: LigandFilterConfig) -> str | None:
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors
    except Exception:
        return None

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return "rdkit_invalid_smiles"
    heavy_atoms = mol.GetNumHeavyAtoms()
    if heavy_atoms > config.max_heavy_atoms:
        return "too_many_heavy_atoms"
    if Descriptors.MolWt(mol) > 900:
        return "molecular_weight_too_high"
    return None


def safe_name(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in "-_" else "_" for char in value.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned[:64] or "ligand"

