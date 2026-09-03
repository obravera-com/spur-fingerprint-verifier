"""Every manifest under fixtures/ must recompute cleanly. This is the conformance suite."""
from pathlib import Path

import pytest

from spur_fingerprint_verifier import verify

ROOT = Path(__file__).resolve().parent.parent / "fixtures" / "fingerprint"
OUTCOMES = verify.run_tree(ROOT)


@pytest.mark.parametrize("outcome", OUTCOMES, ids=[f"{o.manifest.parent.name}/{o.vector_id}" for o in OUTCOMES])
def test_vector(outcome):
    assert outcome.ok, "\n".join(outcome.problems)
