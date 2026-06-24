from __future__ import annotations

import html
import json
from dataclasses import dataclass
from pathlib import Path

from .boltzio import load_manifest


@dataclass(frozen=True)
class AffinityResult:
    job_id: str
    ligand_name: str
    smiles: str
    affinity_pred_value: float | None
    affinity_probability_binary: float | None
    source_json: str
    structure_path: str | None


def collect_affinity_results(run_dir: str | Path) -> list[AffinityResult]:
    base = Path(run_dir)
    manifest = _optional_manifest(base)
    by_job = {job["job_id"]: job for job in manifest.get("jobs", [])}
    results: list[AffinityResult] = []

    for json_path in base.rglob("*.json"):
        if json_path.name == "manifest.json":
            continue
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not _looks_like_affinity(payload):
            continue
        job_id = _job_id_from_path(json_path, by_job)
        job = by_job.get(job_id, {})
        results.append(
            AffinityResult(
                job_id=job_id,
                ligand_name=str(job.get("ligand_name", job_id)),
                smiles=str(job.get("smiles", "")),
                affinity_pred_value=_number(payload.get("affinity_pred_value")),
                affinity_probability_binary=_number(payload.get("affinity_probability_binary")),
                source_json=str(json_path),
                structure_path=_find_structure_path(base, job_id, json_path),
            )
        )

    return sorted(
        results,
        key=lambda item: (
            item.affinity_probability_binary is None,
            -(item.affinity_probability_binary or 0.0),
            item.affinity_pred_value is None,
            item.affinity_pred_value or 999999.0,
        ),
    )


def write_html_report(run_dir: str | Path, output_path: str | Path) -> None:
    base = Path(run_dir)
    output = Path(output_path)
    results = collect_affinity_results(base)
    manifest = _optional_manifest(base)
    rows = "\n".join(render_row(index, result) for index, result in enumerate(results, start=1))
    if not rows:
        rows = '<tr><td colspan="8" class="empty">No Boltz affinity JSON files found yet.</td></tr>'
    target = manifest.get("target", {})
    accepted_count = int(manifest.get("accepted_count", 0) or 0)
    rejected_count = int(manifest.get("rejected_count", 0) or 0)
    completed_count = len(results)
    remaining_count = max(accepted_count - completed_count, 0)
    best_probability = _format_number(results[0].affinity_probability_binary) if results else "pending"
    best_ligand = results[0].ligand_name if results else "pending"
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TinyBoltz Report</title>
  <style>
    :root {{
      --ink: #122025;
      --muted: #5d7077;
      --line: #d8e1e5;
      --panel: #ffffff;
      --soft: #f5f8f9;
      --accent: #087f8c;
      --accent-2: #0f5f6b;
      --warn: #9a5b00;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: linear-gradient(180deg, #eef6f7 0, #ffffff 340px);
      font-family: Arial, Helvetica, sans-serif;
    }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 34px 24px 54px; }}
    header {{ border-bottom: 1px solid var(--line); padding-bottom: 22px; }}
    h1 {{ margin: 0 0 8px; font-size: 34px; letter-spacing: 0; }}
    h2 {{ margin: 30px 0 12px; font-size: 18px; }}
    .subtitle {{ color: var(--muted); max-width: 860px; line-height: 1.45; }}
    .badge {{
      display: inline-block;
      border: 1px solid #9ed4d9;
      color: var(--accent-2);
      background: #e9f8f9;
      border-radius: 999px;
      padding: 5px 10px;
      font-size: 12px;
      font-weight: 700;
      margin-bottom: 14px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 12px;
      margin-top: 22px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 14px;
      min-height: 94px;
    }}
    .label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; }}
    .value {{ font-size: 24px; font-weight: 700; margin-top: 10px; overflow-wrap: anywhere; }}
    .pipeline {{
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 8px;
      margin-top: 14px;
    }}
    .stage {{
      border: 1px solid var(--line);
      background: var(--soft);
      border-radius: 8px;
      padding: 12px;
      min-height: 82px;
    }}
    .stage strong {{ display: block; margin-bottom: 6px; }}
    .stage span {{ color: var(--muted); font-size: 13px; line-height: 1.35; }}
    .notice {{
      border-left: 4px solid var(--warn);
      background: #fff8ed;
      padding: 12px 14px;
      margin-top: 18px;
      color: #4d3514;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      margin-top: 10px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 11px;
      text-align: left;
      vertical-align: top;
      font-size: 14px;
    }}
    th {{ background: #edf4f5; color: #29464e; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; }}
    tr:last-child td {{ border-bottom: 0; }}
    code {{ font-family: Consolas, monospace; font-size: 0.92em; }}
    a {{ color: var(--accent-2); font-weight: 700; }}
    .score {{ font-weight: 700; color: var(--accent-2); }}
    .empty {{ text-align: center; color: var(--muted); padding: 36px; }}
    .footnote {{ color: var(--muted); font-size: 13px; line-height: 1.45; margin-top: 18px; }}
    @media (max-width: 900px) {{
      .cards, .pipeline {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      table {{ display: block; overflow-x: auto; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div class="badge">TinyBoltz Evidence Bundle</div>
      <h1>Frontier Protein-Ligand Screen</h1>
      <p class="subtitle">Target <strong>{html.escape(str(target.get("target_id", "unknown")))}</strong> screened through a reproducible Boltz-2 job manifest. This report ranks candidate ligands by available affinity outputs and preserves the files needed for review.</p>
      <div class="cards">
        <div class="card"><div class="label">Accepted Jobs</div><div class="value">{accepted_count}</div></div>
        <div class="card"><div class="label">Completed</div><div class="value">{completed_count}</div></div>
        <div class="card"><div class="label">Remaining</div><div class="value">{remaining_count}</div></div>
        <div class="card"><div class="label">Rejected</div><div class="value">{rejected_count}</div></div>
        <div class="card"><div class="label">Top Candidate</div><div class="value">{html.escape(best_ligand)} / {best_probability}</div></div>
      </div>
      <div class="notice">Research-use prioritization only. These predictions are not therapies, clinical evidence, or validated hits. Wet-lab validation and calibration are required.</div>
    </header>

    <h2>Screening Pipeline</h2>
    <section class="pipeline">
      <div class="stage"><strong>1. Target</strong><span>Protein sequence imported from FASTA or UniProt.</span></div>
      <div class="stage"><strong>2. Ligands</strong><span>SMILES library parsed from CSV or SMI files.</span></div>
      <div class="stage"><strong>3. Prefilter</strong><span>Duplicates, metals, oversized molecules, and invalid strings removed.</span></div>
      <div class="stage"><strong>4. Boltz YAML</strong><span>One affinity-ready complex generated per accepted ligand.</span></div>
      <div class="stage"><strong>5. GPU Run</strong><span>Boltz execution remains explicit and resumable.</span></div>
      <div class="stage"><strong>6. Evidence</strong><span>Affinity JSON and structures collected into this report.</span></div>
    </section>

    <h2>Ranked Candidates</h2>
    <table>
      <thead>
        <tr>
          <th>Rank</th>
          <th>Job</th>
          <th>Ligand</th>
          <th>Binder Probability</th>
          <th>Affinity Value</th>
          <th>SMILES</th>
          <th>Structure</th>
          <th>Source</th>
        </tr>
      </thead>
      <tbody>
        {rows}
      </tbody>
    </table>
    <p class="footnote">Affinity fields are parsed from Boltz output JSON. Binder probability is intended for hit-discovery ranking; affinity values should be interpreted only with domain calibration.</p>
  </main>
</body>
</html>
"""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html_doc, encoding="utf-8")


def render_row(index: int, result: AffinityResult) -> str:
    probability = _format_number(result.affinity_probability_binary)
    affinity = _format_number(result.affinity_pred_value)
    return f"""<tr>
  <td>{index}</td>
  <td><code>{html.escape(result.job_id)}</code></td>
  <td>{html.escape(result.ligand_name)}</td>
  <td class="score">{probability}</td>
  <td>{affinity}</td>
  <td><code>{html.escape(result.smiles)}</code></td>
  <td>{_structure_link(result.structure_path)}</td>
  <td><code>{html.escape(result.source_json)}</code></td>
</tr>"""


def _optional_manifest(base: Path) -> dict:
    manifest_path = base / "manifest.json"
    if not manifest_path.exists():
        return {}
    try:
        return load_manifest(manifest_path)
    except Exception:
        return {}


def _looks_like_affinity(payload: dict) -> bool:
    return "affinity_pred_value" in payload or "affinity_probability_binary" in payload


def _job_id_from_path(path: Path, jobs: dict[str, dict]) -> str:
    path_text = str(path)
    for job_id in jobs:
        if job_id in path_text:
            return job_id
    stem = path.stem
    if stem.startswith("affinity_"):
        return stem.removeprefix("affinity_")
    if stem.startswith("affinity-"):
        return stem.removeprefix("affinity-")
    return stem


def _find_structure_path(base: Path, job_id: str, json_path: Path) -> str | None:
    candidates: list[Path] = []
    search_roots = [json_path.parent, base]
    for root in search_roots:
        for suffix in ("*.cif", "*.pdb"):
            candidates.extend(path for path in root.rglob(suffix) if job_id in str(path))
    if not candidates:
        for suffix in ("*.cif", "*.pdb"):
            candidates.extend(json_path.parent.rglob(suffix))
    if not candidates:
        return None
    return str(sorted(candidates, key=lambda path: len(str(path)))[0])


def _number(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_number(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.4g}"


def _structure_link(path: str | None) -> str:
    if not path:
        return ""
    escaped = html.escape(path)
    return f'<a href="{escaped}">structure</a>'
