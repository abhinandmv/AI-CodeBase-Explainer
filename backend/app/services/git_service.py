import os
from git import Repo


def shallow_clone(repo_url: str, dest_dir: str) -> None:
    # If already exists, reuse it
    if os.path.exists(dest_dir) and os.path.isdir(dest_dir) and os.listdir(dest_dir):
        return

    Repo.clone_from(repo_url, dest_dir, depth=1, single_branch=True)