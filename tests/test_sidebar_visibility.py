from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]/"custom_components"/"mytesy"
class SidebarTests(unittest.TestCase):
 def test_panel_matches_js(self):
  py=(ROOT/"schedule_frontend.py").read_text();js=(ROOT/"www/schedule-editor.js").read_text()
  self.assertIn('PANEL_NAME = "mytesy-schedule-panel-1-2-12"',py)
  self.assertIn("customElements.define('mytesy-schedule-panel-1-2-12'",js)
 def test_switch_is_only_visibility(self):
  s=(ROOT/"switch.py").read_text();section=s.split('class TesySidebarVisibilitySwitch')[1]
  self.assertIn('async_set_sidebar_visible',section)
  self.assertNotIn('async_send_command',section)
  self.assertNotIn('setProgramStatus',section)
 def test_no_in_panel_toggle(self):
  self.assertNotIn('id="schedule-toggle"',(ROOT/"www/schedule-editor.js").read_text())
