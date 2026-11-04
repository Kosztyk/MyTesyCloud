"""Regression tests for TESY climate power/heat state separation."""
import importlib.util
import pathlib
import sys
import types
import unittest
from datetime import datetime, timezone, timedelta

# Load status helper independently without requiring a running HA installation.
root = pathlib.Path(__file__).resolve().parents[1] / "custom_components" / "mytesy"
for package in ("homeassistant", "homeassistant.util", "mytesy"):
    module = types.ModuleType(package)
    module.__path__ = []
    sys.modules.setdefault(package, module)
dt = types.ModuleType("homeassistant.util.dt")
dt.utcnow = lambda: datetime.now(timezone.utc)
dt.as_local = lambda d: d.replace(tzinfo=timezone.utc)
dt.as_utc = lambda d: d.astimezone(timezone.utc)
sys.modules["homeassistant.util.dt"] = dt
constants = types.ModuleType("mytesy.const")
constants.TESY_STATE_STALE_MINUTES = 10
sys.modules["mytesy.const"] = constants
spec = importlib.util.spec_from_file_location("mytesy.status", root / "status.py")
module = importlib.util.module_from_spec(spec)
sys.modules["mytesy.status"] = module
spec.loader.exec_module(module)

class PowerStateRegression(unittest.TestCase):
    def test_heating_with_stale_timestamp_stays_on(self):
        old = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        state = {"status": "on", "heating": "on", "updated_at": old}
        self.assertTrue(module.stale_active_state(state))
        self.assertTrue(module.derived_power_on(state))
        self.assertTrue(module.heating_active(state))

    def test_idle_stays_on(self):
        self.assertTrue(module.derived_power_on({"status": "on", "heating": "off"}))
        self.assertFalse(module.heating_active({"status": "on", "heating": "off"}))

    def test_explicit_off_not_overridden_by_heating(self):
        self.assertFalse(module.derived_power_on({"status": "off", "heating": "on"}))
        self.assertFalse(module.heating_active({"status": "off", "heating": "on"}))

    def test_explicit_off(self):
        self.assertFalse(module.derived_power_on({"status": "off", "heating": "off"}))

    def test_missing_status_fallback(self):
        self.assertTrue(module.derived_power_on({"heating": "on"}))

if __name__ == "__main__":
    unittest.main()
