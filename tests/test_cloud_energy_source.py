from pathlib import Path
import unittest
root=Path(__file__).resolve().parents[1]
class CloudEnergyTests(unittest.TestCase):
    def test_preserve_unique_id(self):
        x=(root/'custom_components/mytesy/sensor.py').read_text()
        self.assertIn('f"{mac}_energy_estimated"',x)
        self.assertIn('SensorStateClass.TOTAL_INCREASING',x)
    def test_never_assume_working_time_is_lifetime(self):
        x=(root/'custom_components/mytesy/sensor.py').read_text()
        self.assertIn('"lifetime_energy_kwh", "total_energy_kwh"',x)
        self.assertIn('"local_fallback"',x)
    def test_stats_connected(self):
        x=(root/'custom_components/mytesy/__init__.py').read_text()
        self.assertIn('coordinator._tesy_statistics = stats',x)
