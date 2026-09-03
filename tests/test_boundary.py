"""The record a verifier emits must carry the bounded proposition and nothing that
reads as grounding, entitlement or truth. These tests are the boundary rule in code."""
from pathlib import Path

from spur_fingerprint_verifier import verify

SRC = Path(__file__).resolve().parent.parent / "fixtures/fingerprint/iscc-content-text/sources"
FORBIDDEN_KEYS = {"grounded", "grounding", "entitlement", "licensed", "owner", "authored", "true", "verified_use"}


def _record():
    ref = (SRC / "ref-harbour-01.txt").read_bytes()
    r = verify.match("iscc-content-text", ref, ref, 0.85)
    return r.record({"content_id": "x", "content_url": None, "registrar": None}, {"source_kind": "agent_output"})


def test_proposition_is_similarity_only():
    assert _record()["proposition"] == verify.PROPOSITION == "similarity_only"


def test_record_carries_no_grounding_or_entitlement_claims():
    def keys(d):
        for k, v in d.items():
            yield k
            if isinstance(v, dict):
                yield from keys(v)
    assert not FORBIDDEN_KEYS & set(keys(_record()))


def test_block_mode_reports_unit_ref():
    ref = (SRC / "ref-harbour-01.txt").read_bytes()
    cand = (SRC / "cand-harbour-excerpt-p2.txt").read_bytes()
    r = verify.match("iscc-content-text", ref, cand, 0.85, unit="block")
    assert r.unit_ref == "block:1" and r.verdict == "match"
