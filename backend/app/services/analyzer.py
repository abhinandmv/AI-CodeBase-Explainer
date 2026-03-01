import os
from typing import Dict, Any, List


def _walk_tree(root: str, max_files: int = 800) -> Dict[str, Any]:
    """
    Builds a lightweight tree. Limits total files to avoid huge responses.
    """
    root = os.path.abspath(root)
    file_count = 0

    def build(path: str) -> Dict[str, Any]:
        nonlocal file_count
        name = os.path.basename(path)
        if os.path.isdir(path):
            children = []
            try:
                items = sorted(os.listdir(path))
            except Exception:
                items = []
            for it in items:
                if file_count >= max_files:
                    break
                full = os.path.join(path, it)
                # ignore big hidden folders
                if it in {".git", "__pycache__", ".venv", "node_modules"}:
                    continue
                children.append(build(full))
            return {"name": name, "type": "dir", "children": children}
        else:
            file_count += 1
            return {"name": name, "type": "file"}

    return build(root)


def analyze_repo(repo_path: str) -> Dict[str, Any]:
    py_deps: List[str] = []
    important: List[str] = []

    # super simple: look for pyproject/requirements/README and some src files
    for rel in ["README.md", "pyproject.toml", "requirements.txt"]:
        p = os.path.join(repo_path, rel)
        if os.path.exists(p):
            important.append(rel)

    # quick dependency signals
    req = os.path.join(repo_path, "requirements.txt")
    if os.path.exists(req):
        try:
            with open(req, "r", encoding="utf-8") as f:
                py_deps = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")][:200]
        except Exception:
            py_deps = []

    analysis = {
        "language": "Python",
        "entrypoints": [],
        "dependencies": {"python": py_deps, "node": [], "java": [], "other": []},
        "important_files": important[:50],
        "tree": _walk_tree(repo_path),
    }
    return analysis