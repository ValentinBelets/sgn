import json
import tempfile
import unittest
from pathlib import Path

from traffic_signs.build_viewer import build_viewer

# Minimal fixture — the extension-seam behaviour does not depend on the full
# catalogue, so a couple of signs keeps the test fast and dataset-independent.
FIXTURE_SIGNS = [
    {"sign_no": "R1-1", "title": "Stop", "url": "https://example.test/r1-1",
     "image_url": "https://example.test/r1-1.png", "standard_sign": "Yes", "sizes": []},
    {"sign_no": "W1-2", "title": "Curve", "url": "https://example.test/w1-2",
     "image_url": "https://example.test/w1-2.png", "standard_sign": "No", "sizes": []},
]


class ViewerExtensionSeamTests(unittest.TestCase):
    """The public viewer must be block-agnostic and expose the SignViewerExt seam.

    A viewer extension (such as the ERM block-insertion layer) lives entirely in
    catalogue.ext.* assets, injected at runtime through the mount + hooks below.
    """

    def _build(self, tmp_dir: str, with_ext: bool = False) -> str:
        tmp = Path(tmp_dir)
        (tmp / 'signs.json').write_text(json.dumps(FIXTURE_SIGNS), encoding='utf-8')
        if with_ext:
            # Self-contained stand-in for an extension, not the real assets.
            (tmp / 'catalogue.ext.css').write_text('/* stub */', encoding='utf-8')
            (tmp / 'catalogue.ext.js').write_text('/* stub */', encoding='utf-8')
        out = tmp / 'catalogue_test.html'
        build_viewer(str(tmp / 'signs.json'), str(out))
        return out.read_text(encoding='utf-8')

    def test_viewer_emits_mount_and_hooks_but_no_block_ui(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            html = self._build(tmp_dir, with_ext=False)

            # Seam: empty per-card mount + init/renderCard hooks.
            self.assertIn('class="sign-ext"', html)
            self.assertIn('SignViewerExt.init', html)
            self.assertIn('SignViewerExt.renderCard', html)

            # Agnostic: no block-insertion UI or matching code in public output.
            for needle in ('block-copy-btn', 'copyBlockCommand', 'block-match-select', 'renderBlockRow'):
                self.assertNotIn(needle, html)

            # No extension present → no asset tags and no leftover placeholder or
            # blank indentation line (output stays byte-clean).
            self.assertNotIn('catalogue.ext.js', html)
            self.assertNotIn('catalogue.ext.css', html)
            self.assertNotIn('%EXT_HEAD%', html)
            self.assertNotIn('    \n</head>', html)

    def test_viewer_links_extension_assets_when_present(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            html = self._build(tmp_dir, with_ext=True)

            self.assertIn('catalogue.ext.css', html)
            self.assertIn('catalogue.ext.js', html)


if __name__ == '__main__':
    unittest.main()
