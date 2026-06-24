from __future__ import annotations


def cache_model(repo_id: str, revision: str | None = None, cache_dir: str | None = None) -> str:
    try:
        from huggingface_hub import snapshot_download
    except Exception as exc:
        raise RuntimeError("Install huggingface_hub or use: python -m pip install -e '.[hf]'") from exc

    return snapshot_download(repo_id=repo_id, revision=revision, cache_dir=cache_dir)

