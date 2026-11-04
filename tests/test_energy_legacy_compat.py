"""Regression guards for old energy statistics identity."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class TestLegacyEnergy(unittest.TestCase):
    def test_legacy_unique_id_and_name(self):
        text = (ROOT / 'custom_components/mytesy/sensor.py').read_text()
        cls = text.split('class TesyCloudEstimatedEnergySensor(', 1)[1]
        self.assertIn('f"{mac}_energy_estimated"', cls)
        self.assertIn('Energy (estimated)"', cls)
        self.assertIn('SensorStateClass.TOTAL_INCREASING', cls)
        self.assertIn('RestoreEntity', text)
    def test_rolling_has_different_identity(self):
        text = (ROOT / 'custom_components/mytesy/sensor.py').read_text()
        cls = text.split('class TesyCloudRollingEnergySensor(', 1)[1].split('class TesyCloudHistoryHoursSensor',1)[0]
        self.assertIn('f"{mac}_energy_rolling_30d"', cls)
        self.assertIn('_attr_state_class = None', cls)
    def test_initial_restore_no_zero_written(self):
        text = (ROOT / 'custom_components/mytesy/sensor.py').read_text()
        self.assertIn('if not self._initialized:', text)
        self.assertIn('return None', text)
    def test_climate_patch_remains(self):
        text = (ROOT / 'custom_components/mytesy/status.py').read_text()
        self.assertIn('return derived_power_on_raw(state)', text)
