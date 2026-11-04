"""Regression: Home Assistant custom panel must use the defined JS tag."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "mytesy"

class TestSchedulePanelRegistration(unittest.TestCase):
    def test_panel_tag_and_asset_version_match(self):
        py = (ROOT / "schedule_frontend.py").read_text()
        js = (ROOT / "www/schedule-editor.js").read_text()
        panel = re.search(r'PANEL_NAME\s*=\s*"([^"]+)"', py).group(1)
        self.assertIn(f"customElements.define('{panel}'", js)
        self.assertIn("schedule-editor-1.2.12.js", py)
        self.assertIn('"version": "1.2.12"', (ROOT / "manifest.json").read_text())

if __name__ == "__main__": unittest.main()
