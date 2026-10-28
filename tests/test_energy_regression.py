"""Regression tests for v1.1.5 energy metadata and accounting."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class TestEnergyRegression(unittest.TestCase):
    def test_rolling_sensor_is_not_measurement(self):
        source = (ROOT / "custom_components/tesy/sensor.py").read_text()
        cls = source.split("class TesyCloudEstimatedEnergySensor", 1)[1].split("class TesyCloudHistoryHoursSensor", 1)[0]
        self.assertIn("_attr_state_class = None", cls)

    def test_cumulative_sensor_metadata(self):
        source = (ROOT / "custom_components/tesy/sensor.py").read_text()
        cls = source.split("class TesyCloudTotalEnergySensor", 1)[1]
        self.assertIn("SensorStateClass.TOTAL_INCREASING", cls)
        self.assertIn('f"{mac}_energy_total_estimated"', cls)

    def test_history_persistence_and_reset_implementation(self):
        source = (ROOT / "custom_components/tesy/history.py").read_text()
        self.assertIn('"energy_total": self._energy', source)
        self.assertIn('self._energy.pop(mac, None)', source)
        self.assertIn('min(max(0.0, (now - previous_sample).total_seconds()), 120.0)', source)

if __name__ == "__main__":
    unittest.main()
