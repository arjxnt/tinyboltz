from __future__ import annotations

from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True)
class BudgetPlan:
    jobs: int
    completed: int
    remaining: int
    minutes_per_job: float
    batch_size: int
    estimated_gpu_hours: float
    estimated_batches: int


def estimate_budget(
    *,
    jobs: int,
    completed: int = 0,
    minutes_per_job: float = 8.0,
    batch_size: int = 1,
) -> BudgetPlan:
    if jobs < 0 or completed < 0:
        raise ValueError("jobs and completed must be non-negative")
    if minutes_per_job <= 0:
        raise ValueError("minutes_per_job must be positive")
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    remaining = max(jobs - completed, 0)
    gpu_hours = remaining * minutes_per_job / 60.0
    batches = ceil(remaining / batch_size) if remaining else 0
    return BudgetPlan(
        jobs=jobs,
        completed=completed,
        remaining=remaining,
        minutes_per_job=minutes_per_job,
        batch_size=batch_size,
        estimated_gpu_hours=gpu_hours,
        estimated_batches=batches,
    )


def format_budget(plan: BudgetPlan) -> str:
    return "\n".join(
        [
            f"Jobs:                {plan.jobs}",
            f"Completed:           {plan.completed}",
            f"Remaining:           {plan.remaining}",
            f"Minutes per job:     {plan.minutes_per_job:g}",
            f"Batch size:          {plan.batch_size}",
            f"Estimated batches:   {plan.estimated_batches}",
            f"Estimated GPU hours: {plan.estimated_gpu_hours:.2f}",
        ]
    )

