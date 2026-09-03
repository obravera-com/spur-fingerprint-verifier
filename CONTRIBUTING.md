# Contributing

This repository is a reference implementation for the fingerprint schemes module of the SPUR evidence profile. Changes to the module *specification* belong on the SPUR working-group tracker, not here; this repository follows the profile, it does not define it.

## Ground rules

- Open an issue before a pull request that changes a scheme, a threshold, or the manifest format.
- Every scheme ships all six fixture classes (`identical`, `near_duplicate_above`, `near_duplicate_below`, `version_redaction`, `negative_unrelated`, `negative_known_defeat`). The runner fails a manifest that omits one.
- Fixture source material must be CC0, public domain, or otherwise freely redistributable, and every vector records its `licence`.
- Fingerprints are recomputed on every run. Never commit a fixture whose `expected_score` was not produced by `tools/pin_expected_scores.py` against the pinned `iscc-core` version, and review the diff when re-pinning.
- British English in prose, sentence case for headings, `snake_case` for schema fields, RFC 2119 keywords where they carry meaning.

## Developer certificate of origin

Contributions are accepted under the [Developer Certificate of Origin 1.1](https://developercertificate.org/). Sign off each commit (`git commit -s`). No CLA.

## Second implementers

The charter requires two independently implemented verifiers before the module is marked stable. If you are building the second one, you need only `fixtures/**/manifest.json`, the source files they point to, and the algorithm references in the registry (`spur-fingerprint-verifier registry`). Please do not copy this code; an independent implementation that agrees with these manifests is the evidence the profile needs.
