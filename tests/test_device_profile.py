import pathlib
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]

class TestCompatibility(unittest.TestCase):
    def test_energy_identity(self):
        data=(ROOT/'custom_components/mytesy/sensor.py').read_text()
        self.assertIn('f"{mac}_energy_estimated"', data)
        self.assertIn('Energy (estimated)', data)
        self.assertIn('SensorStateClass.TOTAL_INCREASING', data)
    def test_new_read_only_sensors(self):
        data=(ROOT/'custom_components/mytesy/sensor.py').read_text()
        self.assertIn('TesyCloudDeviceProfileSensor(coordinator, mac)',data)
        self.assertIn('TesyCloudProgramSnapshotSensor(coordinator, mac)',data)
        self.assertIn('program_preview',data)
if __name__=='__main__':unittest.main()
