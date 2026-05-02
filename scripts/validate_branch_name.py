#!/usr/bin/env python3
"""
Valida o nome da branch atual.

Formato aceito:  tipo/descricao-com-hifen
Exemplos válidos:
  feat/user-authentication
  fix/login-bug
  docs/update-readme
  chore/42-setup-docker

Branches protegidas (não podem receber commits diretos):
  main, master  →  bloqueadas pelo hook no-commit-to-branch do pre-commit-hooks
"""

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

# tipo/descricao-com-hifen (opcionalmente com número de card: feat/42-descricao)
BRANCH_PATTERN = re.compile(r"^(?P<type>[a-z]+)/(?P<desc>[a-z0-9][a-z0-9\-]*)$")

PROTECTED_BRANCHES = {"main", "master"}


def get_current_branch() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def validate() -> None:
    branch = get_current_branch()

    # Branches protegidas são tratadas pelo no-commit-to-branch,
    # mas adicionamos uma mensagem amigável aqui também
    if branch in PROTECTED_BRANCHES:
        _fail(
            f"Direct commits to '{branch}' are not allowed.\n"
            "  Please create a feature branch: feat/your-description"
        )

    match = BRANCH_PATTERN.match(branch)
    if not match:
        _fail(
            f"Branch name '{branch}' does not match the required format.\n\n"
            "  Expected:  type/short-description-with-hyphens\n"
            "  Examples:  feat/user-authentication\n"
            "             fix/42-login-bug\n"
            "             docs/update-readme\n\n"
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
