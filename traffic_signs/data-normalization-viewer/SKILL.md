---
name: data-normalization-viewer
description: Workflow for analyzing, normalizing, and visualizing inconsistent technical datasets (like traffic signage or regulatory codes). Use when data has varied casing, inconsistent naming conventions, or requires a modern interactive dashboard for stakeholder review.
---

# Data Normalization & Viewer Workflow

This skill provides a structured approach to transforming messy technical datasets into standardized repositories with accompanying interactive dashboards.

## Workflow

### 1. Analysis Phase
- Identify unique values in key fields (e.g., `sign_no`, `technical_reference`).
- Use `grep_search` or custom Python scripts to find casing mismatches, extra metadata in fields, and null-value variations (e.g., `-`, `N/A`, `&nbsp;`).

### 2. Normalization Phase
- Develop regex-based logic to unify values while preserving critical technical nuances (e.g., lowercase 'n' for NSW-specific codes).
- Standardize technical citations (e.g., `AS 1742.x` -> `AS1742.x (Description)`).
- Extract extra metadata from primary fields into structured attributes.

### 3. Reporting & Feedback Loop
- Generate a `patch.json` report documenting every change made.
- Export unique technical references to a `mapping.csv` for human-in-the-loop review.
- Provide professional email templates for communicating findings to stakeholders.

### 4. Visualization Phase
- Build a modern dashboard (HTML/JS) using `assets/dashboard_template.html`.
- **Key Features**:
    - Multi-select checkbox groups for categorical filtering (e.g., Series).
    - Multi-select dropdowns for technical standards.
    - Advanced search across multiple fields.
    - Status tags (Superseded, Not NSW, etc.).

## Resources

- `scripts/normalize_data.py`: Template for regex-based data cleaning.
- `assets/dashboard_template.html`: Base for the modernized interactive viewer.

## Guidelines
- **Preserve Nuance**: Do not over-normalize if specific casing or symbols carry technical meaning (e.g., `(R)` for right-facing).
- **Stakeholder Transparency**: Always generate a patch file before finalizing "unified" data.
