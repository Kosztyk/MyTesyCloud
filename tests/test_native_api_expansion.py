"""Offline safeguards against changing legacy energy and introducing unsafe API changes."""
import ast
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/"custom_components"/"mytesy"
class TestNativeExpansion(unittest.TestCase):
    def test_all_modules_compile(self):
        for p in ROOT.glob("*.py"):
            ast.parse(p.read_text(),filename=str(p))
    def test_original_energy_identity_unchanged(self):
        text=(ROOT/"sensor.py").read_text()
        self.assertIn('f"{mac}_energy_estimated"',text)
        self.assertIn('SensorStateClass.TOTAL_INCREASING', text)
        self.assertIn('f"{mac}_energy_rolling_30d"',text)
    def test_cloud_paths_and_request_isolation(self):
        api=(ROOT/"api.py").read_text()
        for endpoint in ("get-device-power-stat","get-device-temp-stat","get-device-state-stat"):
            self.assertIn(endpoint,api)
        stats=(ROOT/"statistics.py").read_text()
        self.assertIn('except Exception',stats)
    def test_mobile_app_command_contracts(self):
        sw=(ROOT/"switch.py").read_text()
        num=(ROOT/"number.py").read_text()
        for command in ("setAdaptiveStart","setAntiFrost","setOpenedWindow","setLockDevice","setUV","setProgramStatus"):
            self.assertIn(command,sw)
        for command in ("setComfortTemp","setEcoTemp","setTCorrection"):
            self.assertIn(command,num)
    def test_schedule_validation(self):
        init=(ROOT/"__init__.py").read_text()
        self.assertIn('vol.Range(min=1, max=255)',init)
        self.assertIn('"deleteProgram"',init)
        self.assertNotIn('"deleteAllPrograms"',init)
if __name__ == "__main__": unittest.main()
