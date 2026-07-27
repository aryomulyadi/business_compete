"""Object storage adapter. Local files are allowed only outside production."""
from __future__ import annotations

import os
from pathlib import Path

import requests


def upload_bytes(pathname: str, content: bytes, content_type: str) -> str:
    token = os.getenv("BLOB_READ_WRITE_TOKEN")
    if not token:
        if os.getenv("VERCEL") == "1":
            raise RuntimeError("BLOB_READ_WRITE_TOKEN is required in Vercel production")
        target = Path("output") / pathname
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return str(target.resolve())
    response = requests.put(
        f"https://blob.vercel-storage.com/{pathname}",
        headers={"Authorization": f"Bearer {token}", "x-add-random-suffix": "0", "x-allow-overwrite": "1", "x-content-type": content_type},
        data=content,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["url"]


def read_text(location: str) -> str:
    if location.startswith(("https://", "http://")):
        headers = {"Authorization": f"Bearer {os.getenv('BLOB_READ_WRITE_TOKEN', '')}"}
        response = requests.get(location, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    return Path(location).read_text("utf-8")


def read_bytes(location: str) -> bytes:
    if location.startswith(("https://", "http://")):
        headers = {"Authorization": f"Bearer {os.getenv('BLOB_READ_WRITE_TOKEN', '')}"}
        response = requests.get(location, headers=headers, timeout=30)
        response.raise_for_status()
        return response.content
    return Path(location).read_bytes()
