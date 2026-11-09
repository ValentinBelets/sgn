# ADR 0001: Unified Normalization Strategy for TfNSW Reporting

## Status
Proposed

## Context
The NSW Traffic Signs dataset contains significant naming inconsistencies across metadata, image filenames, and PDF design plans. To officially communicate these issues to TfNSW, we need a consistent strategy for proposing "fixes." 

There were two primary tensions in defining the "Canonical" name:
1. Whether size/orientation modifiers should be part of the identifier.
2. How to reconcile differences between a filename (e.g., `g1-1.gif`) and metadata (e.g., `G1-1 (L)`).

## Decision
We will adopt a **Unified Correction (Option C)** approach governed by a **Normalization Precedence Rule**.

1. **Canonical Sign Code**: Strictly limited to the base design (e.g., `G1-1`).
2. **Metadata Separation**: Orientation `(L)`, Size `[A]`, and NSW Variants `n` are treated as distinct modifiers/attributes, not part of the base code.
3. **Target format**: `Base + Variant + Orientation + Size` (e.g., `G11-214n(L)[A]`).
4. **Precedence**: All disparate sources (filenames, internal PDF text, JSON metadata) must be corrected to match this Normalized format.

## Consequences
- **Positive**: Enables better grouping and searchability of sign families (e.g., seeing all sizes of `R2-4` together).
- **Positive**: Provides a clear, algorithmic "Target" for TfNSW to update their database.
- **Negative**: May conflict with legacy systems that expect size/orientation to be baked into a single alphanumeric string.
- **Neutral**: Requires a "Fix Reasoning" field to explain why a specific name was chosen when sources clash.
