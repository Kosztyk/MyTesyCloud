"""Offline tests for cumulative energy persistence and metadata."""
import asyncio
import importlib.util
import pathlib
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1] / "custom_components" / "mytesy"
for name in ("homeassistant", "homeassistant.helpers", "homeassistant.util", "mytesy"):
    mod = types.ModuleType(name)
    mod.__path__ = []
    sys.modules.setdefault(name, mod)
core = types.ModuleType("homeassistant.core")
core.HomeAssistant = type("HomeAssistant", (), {})
sys.modules["homeassistant.core"] = core
now = [datetime(2026, 10, 28, 10, 0, tzinfo=timezone.utc)]
dt = types.ModuleType("homeassistant.util.dt")
dt.utcnow = lambda: now[0]
dt.as_local = lambda x: x.replace(tzinfo=timezone.utc)
dt.as_utc = lambda x: x.astimezone(timezone.utc)
dt.DEFAULT_TIME_ZONE = timezone.utc
sys.modules["homeassistant.util.dt"] = dt
constants = types.ModuleType("mytesy.const")
constants.DOMAIN = "mytesy"
constants.TESY_STATE_STALE_MINUTES = 10
sys.modules["mytesy.const"] = constants
memory = {}
class Store:
    def __init__(self, hass, version, key): self.key = key
    async def async_load(self): return memory.get(self.key)
    async def async_save(self, data):
        import copy
        memory[self.key] = copy.deepcopy(data)
storage = types.ModuleType("homeassistant.helpers.storage")
storage.Store = Store
sys.modules["homeassistant.helpers.storage"] = storage
for name in ("status", "history"):
    spec = importlib.util.spec_from_file_location(f"mytesy.{name}", ROOT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"mytesy.{name}"] = module
    spec.loader.exec_module(module)
history = sys.modules["mytesy.history"]

class TestEnergy(unittest.TestCase):
    def setUp(self):
        memory.clear()
        now[0] = datetime(2026, 10, 28, 10, 0, tzinfo=timezone.utc)
    def snapshot(self, heating="on", watts=2000):
        return {"AA": {"state": {"status": "on", "heating": heating, "watt": watts,
              "updated_at": now[0].strftime("%Y-%m-%d %H:%M:%S")}}}
    def test_accumulates_and_survives_restart(self):
        async def run():
            h = history.TesyHistoryManager(None, "test")
            await h.async_load()
            await h.process_snapshot(self.snapshot())
            self.assertEqual(h.get_total_energy_kwh("AA"), 0)
            now[0] += timedelta(seconds=60)
            await h.process_snapshot(self.snapshot())
            self.assertAlmostEqual(h.get_total_energy_kwh("AA"), 2 / 60, places=4)
            h2 = history.TesyHistoryManager(None, "test")
            await h2.async_load()
            self.assertEqual(h2.get_total_energy_kwh("AA"), h.get_total_energy_kwh("AA"))
            await h2.async_reset("AA")
            self.assertEqual(h2.get_total_energy_kwh("AA"), 0)
        asyncio.run(run())
    def test_gap_is_capped(self):
        async def run():
            h = history.TesyHistoryManager(None, "gap")
            await h.async_load()
            await h.process_snapshot(self.snapshot())
            now[0] += timedelta(hours=5)
            await h.process_snapshot(self.snapshot())
            self.assertLessEqual(h.get_total_energy_kwh("AA"), 2*120/3600 + 0.0001)
        asyncio.run(run())
    def test_sensor_metadata(self):
        text = (ROOT / "sensor.py").read_text()
        self.assertIn('key="power_setting"', text)
        self.assertIn('f"{mac}_energy_estimated"', text)
        self.assertIn('f"{mac}_energy_rolling_30d"', text)
        self.assertIn('SensorStateClass.TOTAL_INCREASING', text)
        self.assertIn('Rolling 30-day value can decrease', text)
        self.assertIn('RestoreEntity', text)
        self.assertIn('self.async_get_last_state()', text)

if __name__ == "__main__": unittest.main()
