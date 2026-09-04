"""Fixture runner and fingerprint_match record producer.

Every fingerprint in a manifest is recomputed from the source material on
each run. Stored fingerprints are never trusted; recomputation is the point.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from . import schemes

PROPOSITION = "similarity_only"
VERDICTS = ("match", "no_match")
# Keys that would turn a similarity record into a grounding, entitlement or
# truth claim. The boundary rule forbids them anywhere in a record.
FORBIDDEN_CLAIM_KEYS = frozenset(
    {"verdict", "grounded", "grounding", "entitlement", "licensed", "owner", "authored", "true", "verified_use"}
)
FIXTURE_CLASSES = (
    "identical",
    "near_duplicate_above",
    "near_duplicate_below",
    "version_redaction",
    "negative_unrelated",
    "negative_known_defeat",
)

try:
    _VERSION = version("spur-fingerprint-verifier")
except PackageNotFoundError:  # running from a checkout without install
    _VERSION = "0.0.0+checkout"


def _split_blocks(data: bytes) -> list[bytes]:
    text = data.decode("utf-8")
    return [b.strip().encode("utf-8") for b in re.split(r"\n\s*\n", text) if b.strip()]


@dataclass
class MatchResult:
    scheme_id: str
    scheme_version: str
    unit: str
    reference_fp: str
    candidate_fp: str
    score: float
    threshold: float
    unit_ref: str | None = None

    @property
    def verdict(self) -> str:
        return "match" if self.score >= self.threshold else "no_match"

    def record(self, reference: dict, candidate: dict) -> dict:
        """A fingerprint_match evidence record as proposed for the profile.

        The record carries score and threshold but no verdict; the verdict is
        the consumer's conclusion under their trust policy, not the verifier's
        assertion.
        """
        return {
            "evidence_type": "fingerprint_match",
            "scheme_id": self.scheme_id,
            "scheme_version": self.scheme_version,
            "unit": self.unit,
            "reference": {**reference, "fingerprint": self.reference_fp},
            "candidate": {
                **candidate,
                "fingerprint": self.candidate_fp,
                **({"unit_ref": self.unit_ref} if self.unit_ref else {}),
            },
            "score": self.score,
            "threshold": self.threshold,
            "verifier": {
                "implementation": "spur-fingerprint-verifier",
                "version": _VERSION,
                "computed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            },
            "proposition": PROPOSITION,
        }


def validate_record(record: dict) -> list[str]:
    """Check a fingerprint_match record against the module's requirements.

    Returns a list of problems; an empty list means the record is acceptable.
    A conformant verifier MUST reject a record whose proposition is anything
    other than similarity_only, and the boundary rule forbids keys that read
    as grounding, entitlement or truth claims.
    """
    problems: list[str] = []
    if record.get("evidence_type") != "fingerprint_match":
        problems.append(f"evidence_type is {record.get('evidence_type')!r}, expected 'fingerprint_match'")
    if record.get("proposition") != PROPOSITION:
        problems.append(f"proposition is {record.get('proposition')!r}, expected {PROPOSITION!r}; record MUST be rejected")
    if record.get("scheme_id") not in schemes.REGISTRY:
        problems.append(f"unknown scheme_id {record.get('scheme_id')!r}")
    for field_name in ("score", "threshold"):
        if not isinstance(record.get(field_name), (int, float)):
            problems.append(f"{field_name} is missing or not numeric")

    def keys(d: dict):
        for k, v in d.items():
            yield k
            if isinstance(v, dict):
                yield from keys(v)

    for k in sorted(FORBIDDEN_CLAIM_KEYS & set(keys(record))):
        problems.append(f"record carries forbidden claim key {k!r}")
    return problems


def match(
    scheme_id: str,
    reference: bytes,
    candidate: bytes,
    threshold: float,
    unit: str = "document",
) -> MatchResult:
    scheme = schemes.get(scheme_id)
    cand_fp = scheme.fingerprint(candidate)
    if unit == "block":
        if scheme.media_type != schemes.TEXT:
            raise ValueError(f"{scheme_id} does not support block unit")
        best: tuple[float, str, int] | None = None
        for i, block in enumerate(_split_blocks(reference)):
            fp = scheme.fingerprint(block)
            s = scheme.score(fp, cand_fp)
            if best is None or s > best[0]:
                best = (s, fp, i)
        if best is None:
            raise ValueError("reference has no blocks")
        score, ref_fp, idx = best
        return MatchResult(scheme_id, scheme.scheme_version, unit, ref_fp, cand_fp, score, threshold, f"block:{idx}")
    ref_fp = scheme.fingerprint(reference)
    score = scheme.score(ref_fp, cand_fp)
    return MatchResult(scheme_id, scheme.scheme_version, unit, ref_fp, cand_fp, score, threshold)


@dataclass
class VectorOutcome:
    manifest: Path
    vector_id: str
    fixture_class: str
    expected_verdict: str
    result: MatchResult
    expected_score: float | None
    problems: list[str]

    @property
    def ok(self) -> bool:
        return not self.problems


def run_manifest(manifest_path: Path) -> list[VectorOutcome]:
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    base = manifest_path.parent
    scheme = schemes.get(m["scheme_id"])
    if m.get("scheme_version") != scheme.scheme_version:
        raise ValueError(
            f"{manifest_path}: manifest scheme_version {m.get('scheme_version')!r} "
            f"does not match registry {scheme.scheme_version!r}"
        )
    threshold = float(m["default_threshold"])
    outcomes = []
    for v in m["vectors"]:
        problems: list[str] = []
        if v["class"] not in FIXTURE_CLASSES:
            problems.append(f"unknown fixture class {v['class']!r}")
        if v["expected_verdict"] not in VERDICTS:
            problems.append(f"unknown expected_verdict {v['expected_verdict']!r}")
        if not v.get("licence"):
            problems.append("vector has no licence field")
        ref = (base / v["reference"]).read_bytes()
        cand = (base / v["candidate"]).read_bytes()
        result = match(m["scheme_id"], ref, cand, v.get("threshold", threshold), v.get("unit", "document"))
        if result.verdict != v["expected_verdict"]:
            problems.append(
                f"verdict {result.verdict} != expected {v['expected_verdict']} (score {result.score}, threshold {result.threshold})"
            )
        exp = v.get("expected_score")
        if exp is not None and abs(result.score - float(exp)) > 1e-9:
            problems.append(f"score {result.score} != expected_score {exp} (recomputation diverged)")
        outcomes.append(VectorOutcome(manifest_path, v["id"], v["class"], v["expected_verdict"], result, exp, problems))
    present = {v["class"] for v in m["vectors"]}
    missing = [c for c in FIXTURE_CLASSES if c not in present]
    if missing:
        outcomes.append(
            VectorOutcome(
                manifest_path, "<manifest>", "-", "-",
                MatchResult(m["scheme_id"], scheme.scheme_version, "-", "", "", 0.0, threshold),
                None, [f"manifest is missing required fixture classes: {', '.join(missing)}"],
            )
        )
    return outcomes


def run_tree(root: Path) -> list[VectorOutcome]:
    manifests = sorted(root.rglob("manifest.json"))
    if not manifests:
        raise FileNotFoundError(f"no manifest.json under {root}")
    out: list[VectorOutcome] = []
    for mp in manifests:
        out.extend(run_manifest(mp))
    return out
