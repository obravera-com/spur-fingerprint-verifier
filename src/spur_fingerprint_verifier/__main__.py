"""Command-line entry point.

    python -m spur_fingerprint_verifier fixtures fixtures/fingerprint
    python -m spur_fingerprint_verifier match --scheme iscc-content-text REF CANDIDATE
    python -m spur_fingerprint_verifier registry
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import schemes, verify


def _cmd_fixtures(args: argparse.Namespace) -> int:
    outcomes = verify.run_tree(Path(args.root))
    failed = 0
    for o in outcomes:
        status = "ok  " if o.ok else "FAIL"
        r = o.result
        line = f"{status} {o.manifest.parent.name:22s} {o.vector_id:28s} {o.fixture_class:22s} score={r.score:<7} verdict={r.verdict}"
        print(line)
        for p in o.problems:
            print(f"      - {p}")
        failed += 0 if o.ok else 1
    print(f"\n{len(outcomes) - failed} passed, {failed} failed")
    return 1 if failed else 0


def _cmd_match(args: argparse.Namespace) -> int:
    ref_path, cand_path = Path(args.reference), Path(args.candidate)
    result = verify.match(args.scheme, ref_path.read_bytes(), cand_path.read_bytes(), args.threshold, args.unit)
    record = result.record(
        reference={"content_id": args.content_id, "content_url": args.content_url, "registrar": args.registrar},
        candidate={"source_kind": args.source_kind},
    )
    problems = verify.validate_record(record)
    if problems:  # a bug in this verifier, not in the inputs
        for p in problems:
            print(f"invalid record: {p}", file=sys.stderr)
        return 1
    print(json.dumps(record, indent=2))
    # The verdict is display only; it is deliberately not part of the record.
    print(f"verdict: {result.verdict} (score {result.score}, threshold {result.threshold})", file=sys.stderr)
    return 0


def _cmd_registry(_: argparse.Namespace) -> int:
    print(json.dumps([s.registry_row() for s in schemes.REGISTRY.values()], indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="spur-fingerprint-verifier")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("fixtures", help="recompute every fixture manifest under ROOT and fail on divergence")
    f.add_argument("root", nargs="?", default="fixtures/fingerprint")
    f.set_defaults(fn=_cmd_fixtures)

    m = sub.add_parser("match", help="compare a candidate to a reference and print a fingerprint_match record")
    m.add_argument("reference")
    m.add_argument("candidate")
    m.add_argument("--scheme", required=True, choices=sorted(schemes.REGISTRY))
    m.add_argument("--threshold", type=float, default=0.85)
    m.add_argument("--unit", default="document", choices=["document", "block"])
    m.add_argument("--content-id", default=None)
    m.add_argument("--content-url", default=None)
    m.add_argument("--registrar", default=None)
    m.add_argument("--source-kind", default="agent_output", choices=["agent_output", "disclosed_corpus", "retrieval_log"])
    m.set_defaults(fn=_cmd_match)

    r = sub.add_parser("registry", help="print the scheme registry rows")
    r.set_defaults(fn=_cmd_registry)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
