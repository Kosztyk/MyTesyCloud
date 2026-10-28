"""Tests guarding TESY heating mode against stale cloud reports."""

import importlib.util
import pathlib
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1] / "custom_components" / "tesy"
for name in ("homeassistant", "homeassistant.util", "tesy"):
    package = types.ModuleType(name)
    package.__path__ = []
    sys.modules.setdefault(name, package)
dt = types.ModuleType("homeassistant.util.dt")
dt.utcnow = lambda: datetime.now(timezone.utc)
dt.as_local = lambda value: value.replace(tzinfo=timezone.utc)
dt.as_utc = lambda value: value.astimezone(timezone.utc)
sys.modules["homeassistant.util.dt"] = dt
const = types.ModuleType("tesy.const")
const.TESY_STATE_STALE_MINUTES = 10
sys.modules["tesy.const"] = const
spec = importlib.util.spec_from_file_location("tesy.status", ROOT / "status.py")
status = importlib.util.module_from_spec(spec)
sys.modules["tesy.status"] = status
spec.loader.exec_module(status)


class TestPowerStateRegression(unittest.TestCase):
    def test_stale_heating_does_not_switch_off(self):
        old = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        state = {"status": "on", "heating": "on", "updated_at": old}
        self.assertTrue(status.stale_active_state(state))
        self.assertTrue(status.derived_power_on(state))
        self.assertTrue(status.heating_active(state))

    def test_idle_is_still_on(self):
        state = {"status": "on", "heating": "off"}
        self.assertTrue(status.derived_power_on(state))
        self.assertFalse(status.heating_active(state))

    def test_explicit_off_wins(self):
        state = {"status": "off", "heating": "on"}
        self.assertFalse(status.derived_power_on(state))
        self.assertFalse(status.heating_active(state))

    def test_normal_off(self):
        self.assertFalse(status.derived_power_on({"status": "off", "heating": "off"}))

    def test_fallback_without_status(self):
        self.assertTrue(status.derived_power_on({"heating": "on"}))


if __name__ == "__main__":
    unittest.main()
