from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BoltzCommand:
    args: list[str]

    def shell_text(self) -> str:
        return " ".join(_quote(arg) for arg in self.args)


def build_boltz_command(
    input_path: str | Path,
    output_dir: str | Path | None = None,
    *,
    use_msa_server: bool = True,
    use_potentials: bool = False,
    accelerator: str | None = None,
    model: str | None = "boltz2",
    override: bool = False,
) -> BoltzCommand:
    args = ["boltz", "predict", str(input_path)]
    if output_dir:
        args += ["--out_dir", str(output_dir)]
    if use_msa_server:
        args.append("--use_msa_server")
    if use_potentials:
        args.append("--use_potentials")
    if accelerator:
        args += ["--accelerator", accelerator]
    if model:
        args += ["--model", model]
    if override:
        args.append("--override")
    return BoltzCommand(args=args)


def run_boltz(command: BoltzCommand) -> int:
    if shutil.which(command.args[0]) is None:
        raise RuntimeError("Could not find the 'boltz' executable. Install Boltz before using --execute.")
    completed = subprocess.run(command.args, check=False)
    return completed.returncode


def _quote(value: str) -> str:
    if not value:
        return '""'
    if any(char.isspace() for char in value):
        return '"' + value.replace('"', '\\"') + '"'
    return value

