"""Check that the cloud integration keeps a distinct domain."""
import json
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "mytesy"

class TestUniqueDomain(unittest.TestCase):
    def test_domain_matches_folder(self):
        self.assertEqual(json.loads((COMPONENT / "manifest.json").read_text())["domain"], "mytesy")
        self.assertIn('DOMAIN = "mytesy"', (COMPONENT / "const.py").read_text())
        self.assertFalse((ROOT / "custom_components" / "tesy").exists())

    def test_release_points_to_new_folder(self):
        content = (ROOT / ".github/workflows/release.yml").read_text()
        self.assertIn("custom_components/mytesy/manifest.json", content)
        self.assertNotIn("custom_components/tesy/", content)

if __name__ == "__main__":
    unittest.main()
