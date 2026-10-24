"""English fallback translation regression test."""
import json
import unittest
from pathlib import Path

COMPONENT = Path(__file__).resolve().parents[1] / "custom_components" / "tesy"

class TranslationFallbackTests(unittest.TestCase):
    def test_english_matches_source(self):
        english = json.loads((COMPONENT / "translations/en.json").read_text(encoding="utf-8"))
        strings = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
        self.assertEqual(english, strings)
        self.assertEqual(english["config"]["step"]["user"]["data"]["username"], "E-mail")
        self.assertIn("auth", english["config"]["error"])
