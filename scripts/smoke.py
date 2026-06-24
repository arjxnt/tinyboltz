from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="tinyboltz-smoke-"))
    try:
        run_dir = tmp / "run"
        env = {"PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"}
        run(
            [
                PYTHON,
                "-m",
                "tinyboltz",
                "screen",
                "--target",
                str(ROOT / "examples" / "targets" / "demo_target.fasta"),
                "--ligands",
                str(ROOT / "examples" / "ligands" / "demo_ligands.smi"),
                "--out",
                str(run_dir),
                "--limit",
                "3",
            ],
            env=env,
        )
        assert (run_dir / "manifest.json").exists()
        assert len(list((run_dir / "inputs").glob("*.yaml"))) == 3

        result_dir = run_dir / "boltz_output" / "predictions" / "L0001_aspirin"
        result_dir.mkdir(parents=True)
        (result_dir / "affinity-L0001_aspirin.json").write_text(
            json.dumps({"affinity_pred_value": 1.2, "affinity_probability_binary": 0.91}),
            encoding="utf-8",
        )

        run([PYTHON, "-m", "tinyboltz", "status", "--run", str(run_dir)], env=env)
        run([PYTHON, "-m", "tinyboltz", "validate", "--run", str(run_dir)], env=env)
        run([PYTHON, "-m", "tinyboltz", "budget", "--run", str(run_dir)], env=env)
        run([PYTHON, "-m", "tinyboltz", "run", "--prepared", str(run_dir), "--remaining-only"], env=env)
        run(
            [
                PYTHON,
                "-m",
                "tinyboltz",
                "report",
                "--run",
                str(run_dir),
                "--out",
                str(run_dir / "report.html"),
                "--csv",
                str(run_dir / "results.csv"),
                "--json",
                str(run_dir / "results.json"),
            ],
            env=env,
        )
        run(
            [
                PYTHON,
                "-m",
                "tinyboltz",
                "plan",
                "--run",
                str(run_dir),
                "--out",
                str(run_dir / "RUNBOOK.md"),
            ],
            env=env,
        )
        assert "0.91" in (run_dir / "report.html").read_text(encoding="utf-8")
        assert (run_dir / "results.csv").exists()
        assert (run_dir / "results.json").exists()
        assert "Estimated GPU hours" in (run_dir / "RUNBOOK.md").read_text(encoding="utf-8")
        print("tinyboltz smoke passed")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run(args: list[str], env: dict[str, str]) -> None:
    merged_env = os.environ.copy()
    merged_env.update(env)
    completed = subprocess.run(args, cwd=ROOT, env=merged_env, text=True, capture_output=True)
    if completed.returncode:
        print(completed.stdout)
        print(completed.stderr, file=sys.stderr)
        raise SystemExit(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
