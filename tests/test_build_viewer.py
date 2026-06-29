import tempfile
import unittest
from pathlib import Path

from traffic_signs.build_viewer import build_viewer

TRAFFIC_SIGNS = Path(__file__).resolve().parent.parent / 'traffic_signs'
SIGN_DATA = TRAFFIC_SIGNS / 'nsw_traffic_signs_unified.json'


class ViewerExtensionSeamTests(unittest.TestCase):
    """The public viewer must be block-agnostic and expose the SignViewerExt seam.

    A viewer extension (such as the ERM block-insertion layer) lives entirely in
    catalogue.ext.* assets, injected at runtime through the mount + hooks below.
    """

    def _build(self, tmp_dir: str, with_ext: bool = False) -> str:
        out = Path(tmp_dir) / 'catalogue_test.html'
        if with_ext:
            # Self-contained: a stand-in extension, not the real private assets.
            (Path(tmp_dir) / 'catalogue.ext.css').write_text('/* stub */', encoding='utf-8')
            (Path(tmp_dir) / 'catalogue.ext.js').write_text('/* stub */', encoding='utf-8')
        build_viewer(str(SIGN_DATA), str(out))
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

            # No extension assets present → neither tag emitted.
            self.assertNotIn('catalogue.ext.js', html)
            self.assertNotIn('catalogue.ext.css', html)

    def test_viewer_links_extension_assets_when_present(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            html = self._build(tmp_dir, with_ext=True)

            self.assertIn('catalogue.ext.css', html)
            self.assertIn('catalogue.ext.js', html)


if __name__ == '__main__':
    unittest.main()
