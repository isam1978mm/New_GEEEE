from __future__ import annotations

import ast
from pathlib import Path


BANNED_CALLS = {"FileResponse", "StreamingResponse", "open", "sendfile"}
BANNED_ATTR_CALLS = {"open"}
APPROVED_FILE = Path("app/services/artifact_response.py").resolve()


def find_violations(root: Path) -> list[str]:
    violations: list[str] = []
    for path in root.rglob("*.py"):
        resolved = path.resolve()
        if resolved == APPROVED_FILE:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in BANNED_CALLS:
                    violations.append(f"{path}:{node.lineno}:{node.func.id}")
                if isinstance(node.func, ast.Attribute) and node.func.attr in BANNED_ATTR_CALLS:
                    violations.append(f"{path}:{node.lineno}:{node.func.attr}")
    return violations


def main() -> int:
    root = Path("app/api")
    violations = find_violations(root)
    if violations:
        for violation in violations:
            print(violation)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
