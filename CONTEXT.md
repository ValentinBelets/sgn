# NSW Traffic Signs Context

## Glossary

### Canonical Sign Code
The primary unique identifier for a traffic sign (e.g., `G1-1`, `R2-4`). It represents the base design of the sign. It **excludes** orientation modifiers (like left/right), size modifiers, or bracketed sub-types.

### Orientation Modifier
Metadata indicating the directionality of a sign, typically found in parentheses in the raw data (e.g., `(L)`, `(R)`, `(LR)`).

### NSW Variant Suffix
The lowercase `n` suffix (e.g., `G11-214n`) indicating that the sign has been specifically modified or designed for use in NSW, as opposed to being a standard Australian sign. This suffix is often subject to placement inconsistencies in the raw data.

### Size Modifier
A letter (e.g., `A`, `B`, `C`) indicating the physical dimensions of the sign. These are treated as metadata rather than part of the Canonical Sign Code, as they typically only proportionally scale the sign.

### Sub-type Modifier
Represented in square brackets (e.g., `[A]`, `[1]`), these indicate variants of a sign that may have a different visual layout or specific application while sharing the same function and base code.

### Normalized Sign Reference Name
The canonical string representation of a sign, constructed by combining the Canonical Sign Code with its Modifiers (e.g., `G11-214n(L)[A]`). This serves as the "source of truth" for comparing disparate data sources.

### Design Plan PDF
A technical drawing file containing detailed specifications and dimensions for a sign.

### Internal PDF Reference
The sign code or name mentioned within the text or title block of a Design Plan PDF. This often differs from external metadata.

### Asset Filename Reference
The sign code or name inferred from the filename of an image (`.gif`, `.png`) or PDF asset.

### Normalization Precedence Rule
The reconciliation strategy where all disparate data sources (Metadata, Asset Filenames, Internal PDF References) are corrected to align with the **Normalized Sign Reference Name** format. This ensures systemic consistency across the entire catalogue.

## Inconsistency Categories

### Critical: Reference Mismatch
A direct contradiction between data sources where a sign identifier points to an entirely different sign design in the associated asset (Image or PDF).

### Major: Variant/Modifier Error
Missing or misplaced critical identifiers such as the **NSW Variant Suffix** (`n`) or **Orientation Modifiers**, which changes the functional meaning of the sign reference.

### Minor: Format Inconsistency
Cases where the information is technically correct but deviates from the **Normalized Sign Reference Name** format (e.g., casing, delimiter usage, or parenthetical style).

### Ambiguous Reference
A single sign identifier that resolves to multiple different sign designs, or multiple identifiers that resolve to the same design without a clear canonical relationship.

### Reference Gap
A case where metadata (Legislative or Technical Reference) is missing ("NA", "Project Specific", or blank) despite a valid reference existing within associated assets (PDF/Image) or being required by national standards.

### Fix Reasoning
The technical justification for a proposed change to a sign's metadata, typically based on cross-referencing between Assets, Standards, and the **Normalization Precedence Rule**.
