from __future__ import annotations

from pathlib import Path


FORBIDDEN_PATTERN = "ee.Authenticate("


def find_violations(*roots: Path) -> list[str]:
    violations: list[str] = []
    for root in roots:
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), start=1):
                if FORBIDDEN_PATTERN in line:
                    violations.append(f"{path}:{lineno}:{FORBIDDEN_PATTERN}")
    return violations


def main() -> int:
    violations = find_violations(Path("app"), Path("tests"))
    if violations:
        for violation in violations:
            print(violation)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
