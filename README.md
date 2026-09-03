# spur-fingerprint-verifier

Reference verifier and conformance fixtures for the **fingerprint schemes module** of the SPUR evidence profile, layered on the [Content Telemetry](https://github.com/SPUR-Coalition/telemetry) standard.

Status: draft, tracking the module proposal on the evidence working-group tracker. Not yet stable; the charter requires a second, independently implemented verifier before that.

## What this does

Given a registered reference item and a candidate (an AI output, a document from a disclosed corpus, an item from a retrieval log), the verifier recomputes both fingerprints under a named scheme and emits a `fingerprint_match` evidence record carrying a score, the threshold applied, and a verdict.

The record supports exactly one proposition, `similarity_only`: *under this scheme, this candidate resembles this reference to this degree.* It does not claim grounding, access, completeness, entitlement or truth. `tests/test_boundary.py` checks that the record schema cannot carry such claims.

## Schemes

| scheme_id | algorithm | unit | measure |
|---|---|---|---|
| `iscc-content-text` | ISO 24138 Content-Code Text | document or block | 1 − Hamming/64 |
| `iscc-data` | ISO 24138 Data-Code | whole file | 1 − Hamming/64 |
| `iscc-instance` | ISO 24138 Instance-Code | whole file | exact |
| `winnowing-text` | Winnowing (SIGMOD 2003), k=25, w=4 | document | Jaccard |

`spur-fingerprint-verifier registry` prints the full registry rows, including each scheme's documented `known_defeats` and `false_positive_profile`.

## Run it

```
pip install -e ".[dev]"
spur-fingerprint-verifier fixtures fixtures/fingerprint
python -m pytest -q
```

The fixture runner recomputes every fingerprint from source on every run and fails on any divergence from the pinned scores or verdicts. CI runs it on a clean Ubuntu checkout under two Python versions, which is the "reproducible from a clean checkout" bar in the charter, made visible.

To compare two files and get a record:

```
spur-fingerprint-verifier match reference.txt candidate.txt --scheme iscc-content-text --unit block \
  --content-id "..." --registrar "..." --source-kind agent_output
```

## Fixture classes

Every scheme ships six classes. The two negatives are as important as the positives: a scheme that documents where it fails is more useful to a consumer's trust policy than one that does not.

| class | purpose |
|---|---|
| `identical` | positive control |
| `near_duplicate_above` | sub-editing, reformatting, encoding changes; must match |
| `near_duplicate_below` | the boundary case two verifiers must agree on |
| `version_redaction` | the same article updated, with paragraphs added or removed; shows where document-level and block-level behaviour diverge |
| `negative_unrelated` | same topic, different source; must not match |
| `negative_known_defeat` | a transformation from the scheme's `known_defeats`; must not match, and the fixture says so is expected |

Something the text fixtures make visible at once: for 64-bit ISCC codes, unrelated content scores around 0.5, so scores in the 0.4 to 0.6 band carry no information, and the ISCC document code drops below threshold on an updated version of the same article while block-level matching and winnowing both hold. That is the case for shipping more than one scheme.

## What this is not

- Not a change to the Content Telemetry wire format. The verifier reads `content_id`, `content_url`, `content_telemetry_id` and `session_id` as the standard defines them and adds nothing to any event.
- Not a registry, a ledger or a service. There is no network access and no dependency beyond `iscc-core`.
- Not ObraVera's product. ObraVera's registry uses the same schemes; this repository exists so that the profile's evidence can be checked by anyone without it.

## Licence

Apache-2.0. Fixture source material is original and released under CC0-1.0. See `NOTICE`.
