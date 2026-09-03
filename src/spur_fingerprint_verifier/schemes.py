"""Scheme registry for the SPUR evidence profile fingerprint module.

Each scheme is a registry row (the descriptive fields the profile requires)
plus two callables: ``fingerprint`` turns a unit of material into a
fingerprint string, and ``score`` compares two fingerprints on the scheme's
stated similarity measure. Scores are normalised so that 1.0 is identical
and 0.0 is unrelated, whatever the underlying measure.

Nothing here depends on any ObraVera service. The only external dependency
is ``iscc-core``, the open reference implementation of ISO 24138.
"""

from __future__ import annotations

import hashlib
import io
import re
from dataclasses import dataclass, field
from typing import Callable

import iscc_core as ic

# Media types understood by the registry.
TEXT = "text"
BINARY = "binary"


@dataclass(frozen=True)
class Scheme:
    scheme_id: str
    scheme_version: str
    algorithm_ref: str
    implementation_ref: str
    media_type: str
    unit: str
    similarity_measure: str
    score_range: str
    known_defeats: tuple[str, ...]
    false_positive_profile: str
    fingerprint: Callable[[bytes], str] = field(repr=False, compare=False)
    score: Callable[[str, str], float] = field(repr=False, compare=False)

    def registry_row(self) -> dict:
        """The descriptive fields only, as they appear in the profile table."""
        return {
            "scheme_id": self.scheme_id,
            "scheme_version": self.scheme_version,
            "algorithm_ref": self.algorithm_ref,
            "implementation_ref": self.implementation_ref,
            "media_type": self.media_type,
            "unit": self.unit,
            "similarity_measure": self.similarity_measure,
            "score_range": self.score_range,
            "known_defeats": list(self.known_defeats),
            "false_positive_profile": self.false_positive_profile,
        }


# ---------------------------------------------------------------------------
# ISCC schemes (ISO 24138), via iscc-core
# ---------------------------------------------------------------------------

_ISCC_IMPL = f"iscc-core {ic.__version__} (https://github.com/iscc/iscc-core)"


def _hamming_similarity(a: str, b: str) -> float:
    """1 - normalised Hamming distance between two 64-bit ISCC unit codes."""
    dist = ic.iscc_distance(a, b)
    return round(1.0 - dist / 64.0, 4)


def _iscc_text(data: bytes) -> str:
    return ic.gen_text_code_v0(data.decode("utf-8"), bits=64)["iscc"]


def _iscc_data(data: bytes) -> str:
    return ic.gen_data_code_v0(io.BytesIO(data), bits=64)["iscc"]


def _iscc_instance(data: bytes) -> str:
    return ic.gen_instance_code_v0(io.BytesIO(data), bits=64)["iscc"]


def _exact(a: str, b: str) -> float:
    return 1.0 if a == b else 0.0


ISCC_CONTENT_TEXT = Scheme(
    scheme_id="iscc-content-text",
    scheme_version="1.0",
    algorithm_ref="ISO 24138:2024, Content-Code Text (v0)",
    implementation_ref=_ISCC_IMPL,
    media_type=TEXT,
    unit="document or block; block mode compares the candidate to the best-matching reference block",
    similarity_measure="1 - Hamming distance / 64 on the 64-bit Content-Code Text body",
    score_range="0.0 (unrelated) to 1.0 (identical); higher is more similar",
    known_defeats=(
        "full paraphrase that preserves meaning but replaces most surface tokens",
        "translation to another language",
        "excerpts shorter than roughly two sentences, which produce unstable codes",
    ),
    false_positive_profile=(
        "templated or boilerplate text (legal notices, wire-service standing paragraphs) "
        "and very short units score high against each other regardless of origin"
    ),
    fingerprint=_iscc_text,
    score=_hamming_similarity,
)

ISCC_DATA = Scheme(
    scheme_id="iscc-data",
    scheme_version="1.0",
    algorithm_ref="ISO 24138:2024, Data-Code (v0)",
    implementation_ref=_ISCC_IMPL,
    media_type=BINARY,
    unit="whole file",
    similarity_measure="1 - Hamming distance / 64 on the 64-bit Data-Code body (content-defined chunking)",
    score_range="0.0 to 1.0; higher is more similar",
    known_defeats=(
        "re-encoding or recompression of the container",
        "any transformation that rewrites most byte chunks",
    ),
    false_positive_profile="files sharing large identical byte regions (embedded fonts, common headers)",
    fingerprint=_iscc_data,
    score=_hamming_similarity,
)

ISCC_INSTANCE = Scheme(
    scheme_id="iscc-instance",
    scheme_version="1.0",
    algorithm_ref="ISO 24138:2024, Instance-Code (v0), BLAKE3-based",
    implementation_ref=_ISCC_IMPL,
    media_type=BINARY,
    unit="whole file",
    similarity_measure="exact equality of the Instance-Code",
    score_range="0.0 or 1.0",
    known_defeats=("any change to any byte",),
    false_positive_profile="none beyond hash collision",
    fingerprint=_iscc_instance,
    score=_exact,
)


# ---------------------------------------------------------------------------
# Winnowing (Schleimer, Wilkerson and Aiken, 2003)
# ---------------------------------------------------------------------------

_K = 25  # k-gram length in characters after normalisation
_W = 4   # window size


def _normalise(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _winnow(data: bytes) -> str:
    text = _normalise(data.decode("utf-8"))
    if len(text) < _K:
        return ""
    hashes = [
        int.from_bytes(hashlib.blake2b(text[i : i + _K].encode(), digest_size=8).digest(), "big")
        for i in range(len(text) - _K + 1)
    ]
    selected: set[int] = set()
    for i in range(max(1, len(hashes) - _W + 1)):
        window = hashes[i : i + _W]
        selected.add(min(window))
    return ",".join(f"{h:016x}" for h in sorted(selected))


def _jaccard(a: str, b: str) -> float:
    sa = set(a.split(",")) if a else set()
    sb = set(b.split(",")) if b else set()
    if not sa and not sb:
        return 0.0
    return round(len(sa & sb) / len(sa | sb), 4)


WINNOWING_TEXT = Scheme(
    scheme_id="winnowing-text",
    scheme_version="1.0-k25w4",
    algorithm_ref="Schleimer, Wilkerson, Aiken. Winnowing: local algorithms for document fingerprinting. SIGMOD 2003.",
    implementation_ref="this repository, schemes.py (k=25 characters, w=4, BLAKE2b-64 k-gram hashes)",
    media_type=TEXT,
    unit="document; local matches surface as partial Jaccard overlap",
    similarity_measure="Jaccard similarity of selected k-gram hash sets",
    score_range="0.0 to 1.0; higher is more similar",
    known_defeats=(
        "paraphrase at the sentence level",
        "translation",
        "word-order shuffling within sentences",
    ),
    false_positive_profile="shared boilerplate contributes overlap in proportion to its length",
    fingerprint=_winnow,
    score=_jaccard,
)


REGISTRY: dict[str, Scheme] = {
    s.scheme_id: s
    for s in (ISCC_CONTENT_TEXT, ISCC_DATA, ISCC_INSTANCE, WINNOWING_TEXT)
}


def get(scheme_id: str) -> Scheme:
    try:
        return REGISTRY[scheme_id]
    except KeyError:
        raise KeyError(f"unknown scheme_id {scheme_id!r}; registered: {sorted(REGISTRY)}") from None
