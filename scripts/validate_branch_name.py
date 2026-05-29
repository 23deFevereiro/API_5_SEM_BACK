#!/usr/bin/env python3
"""
Valida o nome da branch atual.

Formato aceito:  tipo/descricao-com-hifen
Exemplos válidos:
  feat/SCRUM-11-CSV-Upload
  fix/SCRUM-42-Login-Bug
  chore/SCRUM-12-Requirements-Track-Back

Branches protegidas (não podem receber commits diretos):
  main, master  →  bloqueadas pelo hook no-commit-to-branch do pre-commit-hooks

"""

import os
import re
import subprocess
import sys

ALLOWED_TYPES = [
    "feat",
    "fix",
    "docs",
    "chore",
    "refactor",
    "test",
    "style",
    "ci",
    "perf",
]

BRANCH_PATTERN = re.compile(r"^(?P<type>[a-z]+)/SCRUM-\d+-[a-zA-Z0-9][a-zA-Z0-9\-]*$")

PROTECTED_BRANCHES = {"main", "master"}

EXEMPT_BRANCHES = {"develop", "staging", "release"}


def get_current_branch() -> str:
    github_ref = os.environ.get("GITHUB_HEAD_REF") or os.environ.get("GITHUB_REF_NAME")
    if github_ref:
        return github_ref.strip()

    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def validate() -> None:
    branch = get_current_branch()

    if branch in ("HEAD", ""):
        print("[SKIP] Could not determine branch name, skipping validation.")
        sys.exit(0)

    if branch in PROTECTED_BRANCHES:
        _fail(
            f"Direct commits to '{branch}' are not allowed.\n"
            "  Please create a feature branch: feat/your-description"
        )

    if branch in EXEMPT_BRANCHES:
        print(
            f"[OK] Branch '{branch}' is a long-lived branch, skipping name validation."
        )
        return

    match = BRANCH_PATTERN.match(branch)
    if not match:
        _fail(
            f"Branch name '{branch}' does not match the required format.\n\n"
            "  Expected:  type/SCRUM-11-short-description\n"
            "  Examples:  feat/SCRUM-11-CSV-Upload\n"
            "             fix/SCRUM-42-Login-Bug\n"
            "             chore/SCRUM-12-Requirements-Track-Back\n\n"
            f"  Allowed types: {', '.join(ALLOWED_TYPES)}\n"
            "  Rules: lowercase letters, numbers and hyphens only in description"
        )

    branch_type = match.group("type")
    if branch_type not in ALLOWED_TYPES:
        _fail(
            f"Invalid branch type: '{branch_type}'.\n"
            f"  Allowed types: {', '.join(ALLOWED_TYPES)}"
        )

    print(f"[OK] Branch name OK: {branch}")


def _fail(message: str) -> None:
    print(f"\n[ERROR] Invalid branch name:\n   {message}\n", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    validate()
