# ADR 0002: Cross-Authority Canonical Sign Model

## Status
Proposed

## Context
ADR 0001 defined a **Canonical Sign Code** and normalization strategy for a single
authority (TfNSW). We now want to catalogue multiple Australian road authorities
(NSW, SA, and later VicRoads, QLD TMR, Main Roads WA, …) in one system and answer
two questions uniformly:

1. *Has a given authority's published data changed since we last looked?*
2. *Where do authorities agree or diverge on the same Australian Standards sign?*

Two facts shape the design:

- **Sources are heterogeneous.** NSW is scraped HTML (no API, no timestamps). SA is a
  clean JSON REST API (`…/api/v1/signs`) with `updatedDate`/`updatedBy` on every
  record. Future authorities include PDF catalogues. Each source needs its own
  acquisition logic.
- **Content overlaps heavily, by design.** The absolute majority of signs are
  Australian Standards (AS 1742 series) signs that are *identical* across states.
  Each authority decorates the shared AS base code with its own dialect.

This overlap is empirically confirmed. Joining NSW (`sign_no`) and SA
(`detail[].code`) on a decoration-stripped AS base key (see `scratch/join_nsw_sa.py`,
run 2026-11-09) yields:

| | NSW | SA |
|---|---|---|
| Distinct AS base keys | 1,450 | 1,125 |
| **Shared (exact base match)** | **499** | **499** |

The remaining ~1,580 non-matches are **not** normalizer failures: ~71% are legitimate
state-variant codes (NSW `n` dialect, SA `SA`/`MOD` dialect), 19 are SA drawing
numbers, and the rest are genuine adoption differences (a sign one state catalogues
and the other does not). The match itself is high-precision — zero false matches
observed in sampling.

## Decision

Adopt a **Readers-over-Shared-Mirror** architecture with a hand-owned canonical layer.

### 1. Layer split
- **Source Adapter (Reader)** — one per source, responsible only for turning a source
  (HTML page, REST API, PDF catalogue) into raw rows. Readers are mechanical and
  intended to be *generated* (e.g. printed as agent-native CLIs). A reader knows HTTP,
  pagination, and the source's field layout — nothing about Australian Standards.
- **Canonical Layer (Mirror + Normalizer)** — hand-owned. Reconciles each authority's
  raw dialect to the shared **Canonical Sign Code** (ADR 0001) and stores the result.
  This is the system's IP and is **not** generated.

### 2. Data model
Three row kinds in the mirror:

**`sign` (canonical, shared)** — one row per distinct AS sign.
- `canonical_code` (PK) — AS base, decoration-stripped (e.g. `G1-1`, `D4-1-1`)
- `series` — AS series (e.g. `R4 SPEED`, `G7`)
- `standard` — AS reference where known (e.g. `AS1742.2`)
- `description`

**`authority_ref` (overlay, per authority × canonical sign)** — how one authority
publishes a shared sign.
- `authority` (`NSW`, `SA`, …) + `canonical_code` (FK) — composite key
- `raw_code` — the authority's own string (e.g. `G11-214n(L)[A]`, `D4-1-1A`)
- `variant_marker`, `orientation`, `size`, `subtype` — extracted modifiers
- `edition` — the AS **edition** this authority cites (e.g. `AS1742.2-2009` vs
  `AS1742.2 2022`); null where unpublished
- `legis_ref`, `tech_ref`, `source_url`, asset refs
- `source_type` — `html` | `api` | `pdf`
- `first_seen`, `last_seen`, `changed_at`

**`authority_local` (state-only)** — signs with no AS parent (SA `CS2-DRG-…` drawing
numbers, `D4-SA100`, pure numerics; NSW project-specific signs). Same shape as
`authority_ref` but `canonical_code` is null and a `local_code` carries identity.
These are expected and first-class, not errors.

### 3. Per-authority decoration rulesets (the Normalizer)
The normalizer is a small, explicit, per-authority ruleset mapping `raw_code` →
`canonical_code` + modifiers. Observed rules:

| Concern | NSW | SA |
|---|---|---|
| Variant marker | trailing `n` (`R4-1n` → `R4-1`) | `MOD` suffix = modified; `SA`-infix = **state-local**, do **not** collapse |
| Orientation | `(L)` `(R)` `(LR)` | (rare; same convention) |
| Size | bracketed `[A] [B] [C]` | concatenated trailing letter (`D4-1-1A` → base `D4-1-1`, size `A`); also `S` |
| Sub-type | `[…]` square brackets | — |
| Non-canonical | project-specific | drawing numbers (`CS2-DRG-…`, 5+ digit numerics) → `authority_local` |

**Rule of thumb:** strip orientation/size/sub-type and the authority's variant marker
to reach the canonical base; anything that does not resolve to an AS-catalogue shape
(`^[A-Z]{1,3}\d…`) is `authority_local`. The `SA`-infix is deliberately **not**
collapsed — it denotes an SA-local number, not a variant of a shared base (collapsing
it produced false matches; see join script history).

### 4. Change-detection strategy (per source, unified in the mirror)
- **Timestamped sources (SA):** incremental — pull where `updatedDate > last_sync`;
  record `changed_at` and `updatedBy`.
- **Untimestamped sources (NSW):** full snapshot + content diff against the last
  stored `authority_ref` rows; `changed_at` set when a field changes.
Regardless of mechanism, "what changed for authority X since T" is a uniform query
over `authority_ref.changed_at` / `last_seen`. Rows absent from a fresh pull but
previously `last_seen` are flagged as removed.

### 5. Cross-authority signals (the payoff)
Because shared signs collapse to one `canonical_code`, the mirror answers questions no
single-authority catalogue can:
- **Edition drift** — matched signs whose `authority_ref.edition` disagrees would flag
  a state lagging a standard revision (potentially the highest-value signal). **Not
  achievable from current sources** (see note below); it is a target, not a capability.
- **Standard-part agreement** — matched signs should agree on the governing AS part
  (e.g. `AS1742.2`). Empirically they do: an 80-sign sample of the 499 matches agreed
  68/68 where both sides published a part (~99%), with one high-signal anomaly
  (`G7-11`: NSW `AS2890.1` vs SA `AS1742.6`). This is the achievable cross-check today
  and independently corroborates the canonical key.
- **Divergence alarms** — if authorities that historically agreed on a canonical sign
  start disagreeing, that is either a genuine new variant or a broken reader.

> **Edition-data availability (2026-11-09, `scratch/edition_sample.py`).** Edition-drift
> detection is currently blocked on *both* sides: NSW publishes the AS part but **never
> an edition year**; SA *has* editioned references (`AS1742.2-2009` vs `AS1742.2 2022`)
> in its `/references` table but links signs to the **part-only** reference, so no
> per-sign edition is resolvable. Realising this signal requires a source that pins a
> sign to a specific edition — most likely the Design Plan PDFs (ADR 0001), not the
> authority metadata.

## Consequences
- **Positive** — Readers are disposable/generated; the valuable, fragile logic
  (normalizer) is small (~6 rules/authority), explicit, and version-controlled.
- **Positive** — ~500 signs already dedupe across two maximally-different sources,
  proving the key before any build.
- **Positive** — Change detection and cross-authority comparison are the *same* query
  surface over one mirror, not N bespoke scripts.
- **Negative** — Base-code match proves *same AS catalogue number*, not *same
  artwork/edition*. The standard-part axis is available and corroborates the key
  (~99% agreement in sample); the edition axis is **not** available from NSW or SA
  metadata and needs a third source (PDFs) before edition-drift detection is possible.
- **Negative** — Each new authority needs a hand-authored decoration ruleset; the
  normalizer cannot be fully generated.
- **Neutral** — The `SA`-infix ambiguity shows canonical-key rules are authority-
  specific judgement calls and must be documented per authority as they are added.

## References
- ADR 0001 — Unified Normalization Strategy (single-authority canonical code)
- `scratch/join_nsw_sa.py` — NSW↔SA canonical join (evidence for this ADR)
- `scratch/edition_sample.py` — standard-part cross-check & edition-availability finding
- NSW source: scraped HTML (`traffic_signs/scrape_signs.py`)
- SA source: `https://…/Production/api/v1/{signs,series,references,designs}`
