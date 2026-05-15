# NSW Traffic Signs Catalogue

Static catalogue and data-processing tools for NSW traffic sign data.

## Repository layout

- `traffic_signs/`: published site, datasets, and processing scripts
- `traffic_signs/images/`: downloaded sign images
- `scratch/`: exploratory scripts and sample HTML snapshots
- `.github/workflows/deploy-pages.yml`: GitHub Pages deployment (publishes `traffic_signs/`)

## Canonical output

GitHub Pages serves `traffic_signs/index.html`, which redirects to `traffic_signs/interactive_catalogue_unified.html`.

## Typical workflow

1. Scrape source data:
   - `python traffic_signs/scrape_signs.py`
2. Generate normalization patch and unified data:
   - `python traffic_signs/generate_patch.py`
3. Build unified viewer HTML:
   - `python traffic_signs/build_viewer.py`
4. Optionally download local images:
   - `python traffic_signs/download_images.py`

## Notes

- Scripts are now path-stable and can be run from repo root or other working directories.
- Runtime logs and local debugging artifacts are ignored by default.
