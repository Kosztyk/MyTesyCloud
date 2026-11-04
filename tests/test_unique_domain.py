"""Guard the MyTESY cloud integration domain against HACS collisions."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
COMPONENT=ROOT/'custom_components'/'mytesy'

class TestUniqueDomain(unittest.TestCase):
    def test_manifest_domain_and_folder(self):
        self.assertEqual(json.loads((COMPONENT/'manifest.json').read_text())['domain'], 'mytesy')
        self.assertIn('DOMAIN = "mytesy"', (COMPONENT/'const.py').read_text())
        self.assertFalse((ROOT/'custom_components'/'tesy').exists())

    def test_scheduler_and_service_namespaces(self):
        frontend=(COMPONENT/'schedule_frontend.py').read_text()
        editor=(COMPONENT/'www'/'schedule-editor.js').read_text()
        self.assertIn('PANEL_PATH = "mytesy-schedules"', frontend)
        self.assertIn("this._hass.callService('mytesy',service,data)",editor)
        self.assertIn("new URL(a.editor_url,location.origin).searchParams.get('mac')===this.mac", editor)

    def test_release_workflow_targets_new_domain(self):
        release=(ROOT/'.github/workflows/release.yml').read_text()
        self.assertIn('custom_components/mytesy/manifest.json', release)
        self.assertIn('1.2.11', release)
        self.assertNotIn('custom_components/tesy/', release)

if __name__=='__main__':
    unittest.main()
