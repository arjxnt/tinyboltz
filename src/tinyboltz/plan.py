from __future__ import annotations

from pathlib import Path

from .budget import estimate_budget
from .status import inspect_run


def write_runbook(
    *,
    run_dir: str | Path,
    output_path: str | Path,
    minutes_per_job: float = 8.0,
    batch_size: int = 1,
) -> None:
    base = Path(run_dir)
    base_text = base.as_posix()
    output = Path(output_path)
    status = inspect_run(base)
    budget = estimate_budget(
        jobs=status.accepted_count,
        completed=status.completed_count,
        minutes_per_job=minutes_per_job,
        batch_size=batch_size,
    )
    lines = [
        "# TinyBoltz Runbook",
        "",
        "## Run State",
        "",
        f"- Run directory: `{base_text}`",
        f"- Accepted jobs: `{status.accepted_count}`",
        f"- Completed jobs: `{status.completed_count}`",
        f"- Remaining jobs: `{status.remaining_count}`",
        f"- Rejected ligands: `{status.rejected_count}`",
        "",
        "## Budget Estimate",
        "",
        f"- Minutes per job: `{budget.minutes_per_job:g}`",
        f"- Batch size: `{budget.batch_size}`",
        f"- Estimated batches: `{budget.estimated_batches}`",
        f"- Estimated GPU hours: `{budget.estimated_gpu_hours:.2f}`",
        "",
        "## Execution Commands",
        "",
        "Dry-run the remaining Boltz work:",
        "",
        "```bash",
        f"tinyboltz run --prepared {base_text} --remaining-only",
        "```",
        "",
        "Execute on a GPU only when ready to spend compute:",
        "",
        "```bash",
        f"tinyboltz run --prepared {base_text} --remaining-only --execute --accelerator gpu",
        "```",
        "",
        "Regenerate the evidence dashboard and data exports:",
        "",
        "```bash",
        f"tinyboltz report --run {base_text} --out {(base / 'report.html').as_posix()} --csv {(base / 'results.csv').as_posix()} --json {(base / 'results.json').as_posix()}",
        "```",
        "",
        "## Interpretation Guardrails",
        "",
        "- Treat results as prioritization signals, not validated hits.",
        "- Check structures and confidence before selecting compounds.",
        "- Compare top-ranked molecules against assay literature when possible.",
        "- Wet-lab validation is required before any biological claim.",
        "",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
