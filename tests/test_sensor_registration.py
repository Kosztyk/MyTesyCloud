"""Catch setup failures caused by stale class references in the sensor platform."""
import ast
import unittest
from pathlib import Path

SENSOR = Path(__file__).resolve().parents[1] / "custom_components/mytesy/sensor.py"

class TestSensorRegistration(unittest.TestCase):
    def test_all_constructed_entity_classes_are_defined(self):
        tree = ast.parse(SENSOR.read_text())
        classes = {node.name for node in tree.body if isinstance(node, ast.ClassDef)}
        setup = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef) and node.name == "async_setup_entry")
        instantiations = {node.func.id for node in ast.walk(setup) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id.startswith("TesyCloud")}
        self.assertTrue(instantiations, "Expected sensor entity constructors")
        self.assertFalse(instantiations - classes, f"Undefined sensor entity classes: {instantiations - classes}")
        self.assertIn("TesyCloudEstimatedEnergySensor", instantiations)
        self.assertIn("TesyCloudRollingEnergySensor", instantiations)

if __name__ == "__main__":
    unittest.main()
