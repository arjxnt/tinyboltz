from __future__ import annotations

from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


UNIPROT_FASTA_URL = "https://rest.uniprot.org/uniprotkb/{accession}.fasta"


def fetch_uniprot_fasta(accession: str, output_path: str | Path, timeout: int = 30) -> Path:
    accession = accession.strip()
    if not accession:
        raise ValueError("UniProt accession is required")
    url = UNIPROT_FASTA_URL.format(accession=accession)
    request = Request(url, headers={"User-Agent": "tinyboltz/0.1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            text = response.read().decode("utf-8")
    except HTTPError as exc:
        raise RuntimeError(f"UniProt returned HTTP {exc.code} for {accession}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach UniProt for {accession}: {exc.reason}") from exc

    if not text.startswith(">") or "\n" not in text:
        raise RuntimeError(f"UniProt response for {accession} did not look like FASTA")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    return output

