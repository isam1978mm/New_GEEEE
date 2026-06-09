from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Sequence

from app.config import Settings
from app.db.session import create_engine, create_session_factory
from app.services.redaction import redact, verify_redacted
from app.services.run_file_inspector import inspect_run
from app.services.storage import ensure_data_dirs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run local diagnostics for a completed or in-progress run.",
    )
    parser.add_argument("--run-id", required=True, help="Run identifier to inspect.")
    parser.add_argument(
        "--no-redact",
        action="store_true",
        default=False,
        help="Skip redaction (not recommended for shared output).",
    )
    return parser


async def run_cli(*, run_id: str, redacted: bool = True) -> int:
    settings = Settings()
    ensure_data_dirs(settings)
    engine = create_engine(settings)
    session_factory = create_session_factory(settings, engine)

    try:
        async with session_factory() as session:
            result = await inspect_run(
                settings=settings,
                session=session,
                run_id=run_id,
                redacted=redacted,
            )
        payload = result.model_dump()
        if redacted:
            verify_redacted(payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
    except Exception as exc:
        error_payload = {
            "error": "diagnostic_failed",
            "message": str(exc),
            "run_id": run_id,
        }
        if redacted:
            error_payload = redact(error_payload)
            verify_redacted(error_payload)
        print(json.dumps(error_payload, indent=2, sort_keys=True), file=sys.stderr)
        return 1
    finally:
        await engine.dispose()

    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return asyncio.run(run_cli(run_id=args.run_id, redacted=not args.no_redact))


if __name__ == "__main__":
    raise SystemExit(main())
