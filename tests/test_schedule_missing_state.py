"""Protect missing-schedule behavior in the frontend and switch."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "mytesy"

class MissingScheduleTests(unittest.TestCase):
    def test_no_sidebar_instructions_in_editor(self):
        js = (ROOT / "www" / "schedule-editor.js").read_text()
        self.assertNotIn("Use the device switch", js)
        self.assertIn("Schedule not reported", js)
        self.assertIn("!this.scheduleReported", js)
    def test_existing_switch_is_kept_but_unavailable_when_cloud_missing(self):
        py = (ROOT / "switch.py").read_text()
        self.assertIn('field == "programStatus"', py)
        self.assertIn('state.get("programStatus") is not None', py)
    def test_schedule_sensor_distinguishes_missing_and_empty(self):
        py = (ROOT / "schedule_sensor.py").read_text()
        self.assertIn('isinstance(raw, (list, dict))',py)
        self.assertIn('program_status_display',py)
