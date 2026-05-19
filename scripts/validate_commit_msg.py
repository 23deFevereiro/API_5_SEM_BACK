#!/usr/bin/env python3
"""
Valida o formato da mensagem de commit.

Formatos aceitos:
  Com card:      tipo(#123): mensagem curta em inglês
  Sem card (RF): tipo(RF-01): mensagem curta em inglês
  Sem card (RNF): tipo(RNF-01): mensagem curta em inglês
"""

import re
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

COMMIT_PATTERN = re.compile(
    r"^(?P<type>[a-z]+)\((?P<id>#\d+|RF\d+|RNF\d+)\): (?P<msg>.+)$"
)

SKIP_PREFIXES = (
    "Merge pull request",
    "Merge branch",
    "Merge remote-tracking branch",
    "Revert ",
)

MAX_FIRST_LINE = 72


def validate(commit_msg_file: str) -> None:
    with open(commit_msg_file, encoding="utf-8") as f:
        lines = f.readlines()

    content_lines = [line for line in lines if not line.startswith("#")]
    if not content_lines:
        _fail("Commit message is empty.")

    first_line = content_lines[0].rstrip()

    if any(first_line.startswith(prefix) for prefix in SKIP_PREFIXES):
        print(f"[SKIP] Auto-generated commit, skipping: {first_line}")
        sys.exit(0)

    if len(first_line) > MAX_FIRST_LINE:
        _fail(
            f"First line too long ({len(first_line)} chars). "
            f"Max: {MAX_FIRST_LINE}.\n"
            f"  Got: {first_line}"
        )

    match = COMMIT_PATTERN.match(first_line)
    if not match:
        _fail(
            f"""Commit message does not match the required format.

  Expected:  type(#123): short message in English
             type(RF-01): short message in English
             type(RNF-01): short message in English

  Got:       {first_line}

  Allowed types: {', '.join(ALLOWED_TYPES)}"""
        )

    commit_type = match.group("type")
    if commit_type not in ALLOWED_TYPES:
        _fail(
            f"Invalid commit type: '{commit_type}'.\n  "
            f"Allowed types: {', '.join(ALLOWED_TYPES)}"
        )

    print(f"[OK] Commit message OK: {first_line}")


def _fail(message: str) -> None:
    print(f"\n[ERROR] Invalid commit message:\n   {message}\n", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validate_commit_msg.py <commit-msg-file>", file=sys.stderr)
        sys.exit(1)
    validate(sys.argv[1])
