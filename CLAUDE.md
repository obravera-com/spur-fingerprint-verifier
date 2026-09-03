# CLAUDE.md

Working notes for Claude Code sessions in this repository. Read fully before making changes.

## What this repository is

The reference verifier and conformance fixtures for the **fingerprint schemes module** of the SPUR Coalition evidence profile, an optional profile layered on the Content Telemetry standard (https://github.com/SPUR-Coalition/telemetry). The module itself is being proposed on the evidence working-group tracker; `docs/module-proposal.md` is the proposal text and is the design authority for this code. When code and proposal disagree, raise it rather than silently changing either.

Owner: Brady Ridgway (@RedHorseMane on GitHub), founder of ObraVera. The GitHub organisation is `obravera-com`. Standards contributions are made under the personal handle; the code lives under the org.

## Non-negotiables

1. **Boundary rule** (working-group charter): access evidence never becomes proof of grounding, and cryptographic validity never becomes factual truth, completeness or entitlement. The only proposition a `fingerprint_match` record may carry is `similarity_only`. `tests/test_boundary.py` enforces this; never weaken it, and never add fields such as `grounded`, `entitlement`, `owner`, `licensed` to the record.
2. **No core wire-format changes.** This code reads `content_id`, `content_url`, `content_telemetry_id`, `session_id` as the standard defines them and adds nothing to any event. Anything that needs a core hook is a proposal against the standard, not a change here.
3. **Clean-checkout reproducibility.** The only runtime dependency is `iscc-core`, pinned exactly. No network, no service, no ledger, no private ObraVera code. If a change needs anything else, stop and discuss.
4. **Recompute, never trust.** Fingerprints in manifests are recomputed on every run. `expected_score` pins are produced only by `tools/pin_expected_scores.py`; re-pin deliberately and review the diff.
5. **Six fixture classes per scheme**, always, including both negatives. The runner fails a manifest that omits one.
6. **Fixture material is CC0 or public domain**, original where possible, and every vector records `licence`.

## Conventions

British English in prose; sentence case for headings; `snake_case` for schema fields; RFC 2119 keywords only where they carry meaning; DCO sign-off on commits (`git commit -s`). Match the house style of SPUR-Coalition/telemetry.

## Layout

- `src/spur_fingerprint_verifier/schemes.py` — scheme registry; each scheme is a registry row plus `fingerprint()` and `score()`
- `src/spur_fingerprint_verifier/verify.py` — `match()`, `fingerprint_match` record emitter, fixture runner
- `src/spur_fingerprint_verifier/__main__.py` — CLI (`fixtures`, `match`, `registry`)
- `fixtures/fingerprint/<scheme_id>/manifest.json` (+ `sources/`) — conformance vectors
- `tests/` — fixture suite and boundary-rule tests
- `tools/` — deterministic fixture generation and score pinning
- `docs/module-proposal.md` — the working-group proposal this code implements

## Verify before finishing any change

```
pip install -e ".[dev]"
spur-fingerprint-verifier fixtures fixtures/fingerprint
python -m pytest -q
python tools/make_binary_fixtures.py && git diff --exit-code -- fixtures/fingerprint/iscc-data/sources
```

## Roadmap (from the proposal)

- First PR to the working group: profile text, registry table, `fingerprint_match` schema, `iscc-content-text` and `iscc-data` fixtures. Done here; needs porting to the working-group repo's layout once its structure is known.
- Second release: `iscc-content-audio`; align fixture corpus with @erik-sv (cross-evidence interoperability) and @jchomat (C2PA survivability).
- A second, independently implemented verifier from another party is required before the module can be marked stable. Do not write it in this repo.
- Open questions the group has not settled: normative vs recommended thresholds; container for records; `unit_ref` convention for blocks; registry resolution (standard issue #17).
