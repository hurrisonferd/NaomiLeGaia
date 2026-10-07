"""Read-only classifier for an intentional no-checkout Git anchor."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def run(repo: Path, *args: str) -> tuple[int, str, str]:
    process = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    return process.returncode, process.stdout, process.stderr


def main() -> int:
    repo = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    rc, head, err = run(repo, "rev-parse", "HEAD")
    if rc != 0:
        print(json.dumps({
            "status": "NOT_A_GIT_REPOSITORY",
            "repo": str(repo),
            "error": err.strip(),
        }, indent=2))
        return 2

    _, tree, _ = run(repo, "ls-tree", "-r", "--name-only", "HEAD")
    _, index, _ = run(repo, "ls-files")
    _, worktrees, _ = run(repo, "worktree", "list", "--porcelain")
    _, staged_delete, _ = run(repo, "diff", "--cached", "--name-only", "--diff-filter=D", "HEAD")

    tree_count = len([line for line in tree.splitlines() if line.strip()])
    index_count = len([line for line in index.splitlines() if line.strip()])
    staged_delete_count = len([line for line in staged_delete.splitlines() if line.strip()])
    linked = [
        line.split(" ", 1)[1]
        for line in worktrees.splitlines()
        if line.startswith("worktree ")
    ]
    index_path = repo / ".git" / "index"
    index_exists = index_path.exists()

    intentional_candidate = (
        tree_count > 0
        and index_count == 0
        and not index_exists
        and len(linked) >= 2
    )
    status = (
        "INTENTIONAL_NO_CHECKOUT_ANCHOR_CANDIDATE"
        if intentional_candidate
        else "REVIEW_REQUIRED"
    )
    result = {
        "schema": "gaiaos.local-worktree-anchor-check.v1",
        "status": status,
        "repo": str(repo),
        "head": head.strip(),
        "head_tree_count": tree_count,
        "index_count": index_count,
        "index_file_exists": index_exists,
        "staged_delete_count": staged_delete_count,
        "worktree_count": len(linked),
        "worktrees": linked,
        "read_only": True,
        "interpretation": (
            "Empty/missing anchor index plus populated HEAD and linked worktrees is "
            "consistent with an intentional no-checkout anchor; staged-delete-looking "
            "status is not proof of source loss."
            if intentional_candidate
            else "Observed state does not match the narrow intentional-anchor signature; "
            "inspect before changing anything."
        ),
    }
    print(json.dumps(result, indent=2))
    return 0 if intentional_candidate else 1


if __name__ == "__main__":
    raise SystemExit(main())
