from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProteinTarget:
    target_id: str
    sequence: str
    description: str = ""


def read_first_fasta(path: str | Path) -> ProteinTarget:
    fasta_path = Path(path)
    header: str | None = None
    parts: list[str] = []

    for raw_line in fasta_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if header is not None and parts:
                break
            header = line[1:].strip() or fasta_path.stem
            continue
        if header is None:
            raise ValueError(f"{fasta_path} does not look like FASTA: missing header")
        parts.append(line.replace(" ", "").upper())

    if header is None or not parts:
        raise ValueError(f"{fasta_path} does not contain a FASTA sequence")

    target_id, _, description = header.partition(" ")
    sequence = "".join(parts)
    invalid = sorted(set(sequence) - set("ACDEFGHIKLMNPQRSTVWYBXZJUO*-"))
    if invalid:
        raise ValueError(f"{fasta_path} contains unexpected amino-acid symbols: {''.join(invalid)}")

    return ProteinTarget(target_id=safe_id(target_id), sequence=sequence, description=description)


def safe_id(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in "-_" else "_" for char in value.strip())
    return cleaned.strip("_") or "target"

