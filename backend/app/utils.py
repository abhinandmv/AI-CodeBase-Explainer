import hashlib
import re
from pathlib import Path
from typing import Iterable

GITHUB_REPO_RE = re.compile(r"^(https?://)?github\.com/[\w.-]+/[\w.-]+/?$")

def validate_github_repo_url(url: str) -> bool:
    return bool(GITHUB_REPO_RE.match(url.strip()))

def sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def safe_mkdir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)

def iter_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*"):
        if p.is_file():
            yield p

def is_binary_file(path: Path, sample_size: int = 2048) -> bool:
    try:
        data = path.open("rb").read(sample_size)
        return b"\x00" in data
    except Exception:
        return True