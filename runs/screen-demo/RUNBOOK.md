# TinyBoltz Runbook

## Run State

- Run directory: `runs/screen-demo`
- Accepted jobs: `3`
- Completed jobs: `0`
- Remaining jobs: `3`
- Rejected ligands: `2`

## Budget Estimate

- Minutes per job: `8`
- Batch size: `1`
- Estimated batches: `3`
- Estimated GPU hours: `0.40`

## Execution Commands

Dry-run the remaining Boltz work:

```bash
tinyboltz run --prepared runs/screen-demo --remaining-only
```

Execute on a GPU only when ready to spend compute:

```bash
tinyboltz run --prepared runs/screen-demo --remaining-only --execute --accelerator gpu
```

Regenerate the evidence dashboard and data exports:

```bash
tinyboltz report --run runs/screen-demo --out runs/screen-demo/report.html --csv runs/screen-demo/results.csv --json runs/screen-demo/results.json
```

## Interpretation Guardrails

- Treat results as prioritization signals, not validated hits.
- Check structures and confidence before selecting compounds.
- Compare top-ranked molecules against assay literature when possible.
- Wet-lab validation is required before any biological claim.
