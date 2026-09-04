"""The record a verifier emits must carry the bounded proposition and nothing that
reads as grounding, entitlement or truth. These tests are the boundary rule in code."""
from pathlib import Path

from spur_fingerprint_verifier import verify

SRC = Path(__file__).resolve().parent.parent / "fixtures/fingerprint/iscc-content-text/sources"


def _record():
    ref = (SRC / "ref-harbour-01.txt").read_bytes()
    r = verify.match("iscc-content-text", ref, ref, 0.85)
    return r.record({"content_id": "x", "content_url": None, "registrar": None}, {"source_kind": "agent_output"})


def test_proposition_is_similarity_only():
    assert _record()["proposition"] == verify.PROPOSITION == "similarity_only"


def test_record_carries_no_verdict_or_claim_keys():
    def keys(d):
        for k, v in d.items():
            yield k
            if isinstance(v, dict):
                yield from keys(v)
    assert not verify.FORBIDDEN_CLAIM_KEYS & set(keys(_record()))


def test_emitted_record_validates_clean():
    assert verify.validate_record(_record()) == []


def test_foreign_proposition_is_rejected():
    record = _record()
    record["proposition"] = "grounding_proof"
    problems = verify.validate_record(record)
    assert any("MUST be rejected" in p for p in problems)


def test_forbidden_claim_key_is_rejected():
    record = _record()
    record["reference"]["entitlement"] = "licensed"
    problems = verify.validate_record(record)
    assert any("forbidden claim key 'entitlement'" in p for p in problems)


def test_block_mode_reports_unit_ref():
    ref = (SRC / "ref-harbour-01.txt").read_bytes()
    cand = (SRC / "cand-harbour-excerpt-p2.txt").read_bytes()
    r = verify.match("iscc-content-text", ref, cand, 0.85, unit="block")
    assert r.unit_ref == "block:1" and r.verdict == "match"
