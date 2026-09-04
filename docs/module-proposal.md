# [evidence-profile] Fingerprint schemes module: bounded proposition, scheme registry, trust-policy fields and fixture plan

**Affiliation:** Brady Ridgway, founder of ObraVera, which runs an ISCC-based (ISO 24138) fingerprinting and registry implementation in production. Filed as an individual contributor under CONTRIBUTING.md. Any reference verifier ObraVera publishes will be Apache-2.0 and is intended to be one of the two independent implementations the charter requires, not the only one.

**History:** This follows my offer on #18 and the dispositions on #16 and #17. #16 proposed optional `content_iscc` and `excerpt_iscc` fields on the grounding and citation data profiles and was declined as a core change, with content-derived fingerprinting moved to the evidence profile. This issue is the module-level version of that work: nothing here touches the event schema, and the fingerprints that #16 would have placed on the event now live in a verifier-produced evidence record instead. #17 (normative `content_id` scheme resolution) remains a core question and is not reopened here; where this module depends on resolution it says so and treats it as a consumer-policy matter.

**References:** Charter (scope item 1, boundary rule, deliverables and bar); standard issues #16, #17, #18 (disposition of 12 August, four-module consolidation); Content Telemetry 1.0 §4.4 (source roles), §4.5 (content identification), §6.4–6.5 (content and excerpt hashes), §6.8 (evidence references).

---

## 1. Motivation and scope

Content Telemetry gives a content owner an agent-reported record of `content_retrieved`, `content_grounded`, `content_cited`, `content_presented` and `content_engaged`. §4.4 records that grounding, citation and presentation events are reported by the agent only, because they are not observable from the content owner's infrastructure; only the retrieval stage has an origin-side counterpart the owner can correlate against (§7.2). The VPTS module (#18) addresses this forward, by seeding markers before use. This module addresses it backward: given an AI output, a disclosed corpus or a retrieval log, can a consumer establish, to a stated confidence and under a named scheme, that material in it derives from a registered content item, without any cooperation from the reporting agent?

Fingerprint evidence is the only evidence type in the profile that survives the removal of metadata, credentials and markers, and that can be applied to material produced before any telemetry existed. That is also its limit: it says something about content similarity and nothing about how the similarity arose.

The standard's own open-questions list asks for exactly this class of work: "mechanisms that test truthfulness and completeness rather than origin, such as sampled audits or publisher-seeded canary content, are of particular interest." Seeded canary content is the VPTS module (#18); fingerprint matching is the corresponding mechanism for material that was never seeded.

In scope for this module:

- a registry of fingerprint schemes, each with a stable identifier, a versioned algorithm reference, its unit of comparison, and its documented failure modes
- the `fingerprint_match` evidence record and the bounded proposition it supports
- the trust-policy fields a consumer uses to accept or reject a scheme and a threshold
- the mapping of fingerprint workflows to V0–V3
- conformance fixtures, including negative vectors, and a Python reference verifier reproducible from a clean checkout

Out of scope, per the charter:

- any change to the core wire format or event semantics; the module reads `content_id`, `content_url`, `content_telemetry_id` and `session_id` as the standard defines them and adds nothing to the event
- any conclusion about grounding, entitlement, ownership, price or compensation
- accreditation and the conformance mark

## 2. Bounded proposition

The module supports exactly one proposition, stated per evidence record:

> Under scheme *S* at version *v*, the compared unit of material *M* matches registered content item *C* with score *x* against the scheme's stated similarity measure, where *x* meets or exceeds the threshold *t* declared in the consumer's trust policy.

The proposition is a statement about similarity between two artefacts. Under the boundary rule it MUST NOT be read as any of the following, and the profile text will say so in normative language:

- **Not proof of grounding.** A match between an agent's output and *C* does not establish that *C* entered the agent's generation context. The same text may have been reached through another copy, a quotation in a third source, or common phrasing. A `fingerprint_match` record MAY be presented alongside a `content_grounded` event as corroboration; it does not verify that event.
- **Not proof of access or retrieval.** The module does not observe the agent. It cannot distinguish direct retrieval from indirect derivation.
- **Not completeness.** Absence of a match is not evidence of non-use. Every registered scheme has documented transformations that defeat it (§4).
- **Not entitlement or authorship.** A match to *C* says nothing about who holds rights in *C*, whether use was licensed, or whether *C* itself was original. Registration timestamps are evidence of when a fingerprint was recorded, not of when or by whom the content was created.
- **Not cryptographic truth.** A signed fingerprint record proves that a named party asserted a fingerprint at a time; it does not prove the fingerprint was computed correctly or that the underlying content was what the party claims. Recomputation from the reference content is the only check on that, which is why fixtures require recomputability.

A consumer's settlement or dispute process MAY combine a fingerprint match with other modules' evidence (seeded observations, recomputable attribution, entitlement credentials) under its own policy. The combination rule belongs to the consumer's trust policy, not to this module.

## 3. Scheme registry

Each scheme is registered with the following fields (proposed schema names, snake_case):

| Field | Meaning |
|---|---|
| `scheme_id` | Stable identifier, e.g. `iscc-content-text`, `winnowing-text`, `iscc-content-audio` |
| `algorithm_ref` | Normative reference to the algorithm and version, e.g. ISO 24138:2024 for ISCC, the Schleimer/Wilkerson/Aiken paper for winnowing |
| `implementation_ref` | Open implementation the fixtures are computed with, pinned by version |
| `media_type` | Text, image, audio, video or mixed |
| `unit` | Granularity of comparison: document, block, segment, or window, with the parameters that define it |
| `similarity_measure` | How `score` is computed, e.g. Hamming distance on 64-bit Content-Code, Jaccard on selected k-gram hashes |
| `score_range` | Numeric range and direction (higher is more similar, or lower) |
| `known_defeats` | Transformations the scheme is documented not to survive |
| `false_positive_profile` | What kinds of unrelated content produce high scores, e.g. boilerplate, short quotations, templated text |

Initial registry, proposed for the first release:

1. **`iscc-content-text`** — ISCC Content-Code Text (ISO 24138). Document-level and block-level. Chosen as the anchor because it is an ISO standard with an open reference implementation (`iscc-core`), which satisfies the "reproducible from a clean checkout" bar without a bespoke dependency. Block-level correlation (matching an excerpt in an output to a block within a registered document, and surviving version and redaction changes to that document) is the case that motivated #16 and is the one ObraVera has working fixtures for.
2. **`winnowing-text`** — Winnowing k-gram fingerprints for local (excerpt-level) matching where a document-level code is too coarse. Parameters *k* and window *w* are part of the scheme identifier version.
3. **`iscc-content-audio`** — ISCC Content-Code Audio, for spoken and musical audio. Included because audio is the medium where credential stripping is most routine and where SPUR members (broadcasters) have material.
4. **`iscc-data`** and **`iscc-instance`** — exact and near-exact byte-level codes, useful as the trivial positive control in fixtures and for disclosed-corpus matching.

Perceptual image and video schemes are deferred to a second release once a text and audio verifier pair exists. Proposals to add a scheme follow the standard's proposal process and MUST supply the full registry row and at least one negative vector.

## 4. Evidence record

A `fingerprint_match` record is produced by a verifier, not by an agent, and is carried outside the core event stream (in a consumer's evidence store, or attached to a dispute) so that no wire-format change is needed.

```json
{
  "evidence_type": "fingerprint_match",
  "scheme_id": "iscc-content-text",
  "scheme_version": "1.0",
  "unit": "block",
  "reference": {
    "content_id": "...",
    "content_url": "...",
    "fingerprint": "ISCC:...",
    "registered_at": "2026-09-02T09:00:00Z",
    "registrar": "..."
  },
  "candidate": {
    "source_kind": "agent_output | disclosed_corpus | retrieval_log",
    "fingerprint": "ISCC:...",
    "unit_ref": "...",
    "content_telemetry_id": "...",
    "session_id": "..."
  },
  "score": 0.94,
  "threshold": 0.90,
  "verifier": {
    "implementation": "...",
    "version": "...",
    "computed_at": "..."
  },
  "proposition": "similarity_only"
}
```

`content_telemetry_id` and `session_id` are OPTIONAL and present only when the candidate came from a telemetry session, so that a match can be joined to the agent's own report. `proposition` is a fixed string that names the bounded proposition in §2; a record with any other value MUST be rejected by conformant verifiers.

The record deliberately carries `score` and `threshold` but no verdict. Whether a score constitutes a match is the consumer's conclusion under their trust policy (§5), not the verifier's assertion; embedding a verdict in the record would let the record be quoted as a conclusion detached from the threshold that produced it.

Although the record travels outside the event stream, core 1.0 §6.8 defines a `data.evidence` slot on any content event: an array of profile-defined evidence references with `scheme`, `ref` and `digest`, which core does not interpret. This module proposes the convention for its entries: `scheme` is the literal `fingerprint_match`, `ref` is a URI resolving to the record, and `digest` is the SHA-256 of the record's canonical JSON serialisation. This gives a `content_grounded` or `content_cited` event a standard way to point at corroborating fingerprint evidence with no wire-format change.

A record MAY be signed by the verifier. Core 1.0 publishes keys in the manifest (§8.4) but defers signing proof formats — JWS, verifiable credentials — to a later version (§8.9), so the profile, not core, will need to specify the detached-signature format for records; the V2 bar in §6 depends on that profile choice. Per the boundary rule, signature validity establishes only who asserted the record and when.

## 5. Trust-policy fields

A consumer accepts or rejects fingerprint evidence by declaring, per scheme:

| Field | Meaning |
|---|---|
| `accepted_schemes[]` | `scheme_id` and minimum `scheme_version` the consumer will consider |
| `threshold` | Minimum `score` per scheme; the profile ships a recommended default and the rationale, and the consumer MAY tighten it |
| `min_unit_size` | Smallest unit (tokens, seconds, bytes) the consumer will accept a match on, to exclude short-quotation false positives |
| `require_recomputation` | Whether the consumer will recompute the reference fingerprint from the reference content before accepting |
| `accepted_verifiers[]` | Verifier keys or implementations the consumer trusts, if any |
| `registration_before` | Optional: reject matches whose `registered_at` post-dates the candidate, to exclude retrospective registration of someone else's material |

The last field is included deliberately. Fingerprint registries can be gamed by registering content one does not control, and the profile should hand consumers a lever against that rather than pretend the problem does not exist.

## 6. Mapping to V0–V3

Using the workflow-maturity levels from #18 as a frame:

- **V0** — Reference fingerprints are computed and published by the content owner. No candidate comparison. Sufficient for a consumer to recompute and confirm the owner's own records.
- **V1** — A verifier compares candidates from a disclosed corpus or agent output and emits `fingerprint_match` records. Single verifier.
- **V2** — Two independently implemented verifiers produce agreeing records on the conformance fixtures, and records are signed. This is the charter's "stable" bar.
- **V3** — Fingerprint records are anchored to an independent timestamp (transparency log, or the detached provenance anchor @romainbenabdelkader is proposing), so that `registered_at` is itself corroborated rather than asserted.

## 7. Conformance fixtures

Fixtures live under `fixtures/fingerprint/<scheme_id>/` with a manifest listing each vector, the expected score and the expected verdict under the profile's default threshold. Every scheme MUST ship all six classes:

1. **Identical** — candidate equals reference. Positive control.
2. **Near-duplicate above threshold** — minor edits, reformatting, encoding changes, house-style rewording of a lede.
3. **Near-duplicate below threshold** — the boundary case, so that two verifiers can be shown to agree on where the line falls.
4. **Version and redaction** — a later version of the reference with paragraphs added, removed or redacted, where block-level matches persist while the document-level score moves. This class exists so that the profile can show what "the same article, updated" looks like to each scheme, which is the everyday case for news content.
5. **Negative, unrelated** — content on the same topic from an unrelated source, chosen to have similar length and vocabulary. Must not match.
6. **Negative, known defeat** — a transformation from the scheme's `known_defeats` row (paraphrase, translation, heavy excerpting) applied to the reference. Must not match, and the fixture documents that this is expected behaviour rather than a bug.

An exact-match scheme (such as `iscc-instance`) has no near-duplicate band; it MAY satisfy the near-duplicate-above class with its identical vector, and the vector's notes MUST say so.

Fixture source material will be public-domain or CC-licensed text and audio so that the repository stays clean-checkout reproducible; the manifest records the licence per vector. ObraVera's existing block-level, version-handling and redaction fixtures will be re-based onto that material and contributed with the first pull request alongside the `iscc-content-text` and `iscc-data` vectors; `winnowing-text` and `iscc-content-audio` follow in a second.

A runner (`spur-fingerprint-verifier fixtures fixtures/fingerprint`) recomputes every fingerprint from the source material, compares against the manifest, and fails on any divergence. This is deliberately stricter than checking stored fingerprints, because the recomputation is what gives the evidence its value.

## 8. Reference verifiers

I will publish a first verifier (Python, `iscc-core` and a small winnowing implementation, no service dependency, no ledger) under an Apache-2.0 repository and will keep it separate from any ObraVera product code so that it can be read and run in isolation. The charter requires a second independent implementation before the module is marked stable; I would welcome one from any co-author or contributor, and the fixture manifest is designed so that a second implementer needs only the manifest and the algorithm references, not my code.

## 9. Relationship to the other modules

- **Seeded observations (VPTS)** — complementary. Seeded markers give an origin-side counterpart for future use; fingerprints give one for material that was never seeded. A consumer's policy MAY require both for settlement; neither verifies the other.
- **Recomputable attribution** — fingerprint matching is one input an attribution recomputation can consume, provided the attribution module treats it as similarity evidence only.
- **Entitlement credentials** — no coupling. A `fingerprint_match` record carries no entitlement field and MUST NOT be extended with one.
- **C2PA survivability fixtures (@jchomat)** and **cross-evidence interoperability fixtures (@erik-sv)** — I propose the fingerprint fixtures be built on the same source corpus as these, so that the profile can show, on one set of material, which evidence types survive which transformations. Happy to align corpus and manifest format before the first session.

## 10. Open questions for the group

1. Should `threshold` defaults be normative (MUST) or recommended (SHOULD) in the profile? My instinct is SHOULD with a documented rationale, leaving consumers free to tighten.
2. Storage of the record itself stays container-agnostic (consumer evidence store, dispute attachment, or the audit-ledger receipts VPTS proposes), and core §6.8 already provides the event-side reference slot. Does the group accept the `data.evidence` convention proposed in §4 (`scheme` = `fingerprint_match`, `ref` = record URI, `digest` = SHA-256 of the canonical record), or prefer a different entry shape?
3. Block-level identifiers: §4.5 defines `content_id` at document level. Block-level matching needs a `unit_ref` convention. I have used a free-form string above; if the group prefers a structured form I will follow whatever the recomputable-attribution module adopts.
4. Registry resolution: a verifier needs to fetch the reference content (or a stored fingerprint) for a `content_id` in order to recompute. #17 asked for this to be normative in core and is still open. For the module I propose that `reference.registrar` names the resolving registry and that resolution method is a trust-policy choice, so the module works whether or not #17 is adopted. If the group would rather the profile define a resolution record, I can draft one.

## 11. Proposed next steps

- Comments on this issue for two weeks.
- Pull request with `PROFILE.md` text for this module, the registry table, the `fingerprint_match` schema, and the first `iscc-content-text` and `iscc-data` fixtures with the runner.
- I am willing to act as editor for this module and to walk it through at the first working session in October, if the chair and co-authors are content with that.
