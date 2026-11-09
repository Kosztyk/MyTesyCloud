"""Water-heater discovery preserves observations without advertising controls."""
import ast
from pathlib import Path
import runpy
from types import SimpleNamespace
import unittest

COMP = Path(__file__).resolve().parents[1] / "custom_components" / "mytesy"
FAMILIES = runpy.run_path(str(COMP / "device_families.py"))


class CoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator


class WaterHeaterEntity:
    _attr_supported_features = 0

    @property
    def supported_features(self):
        return self._attr_supported_features

    @property
    def operation_list(self):
        return self._attr_operation_list


def load_water_heater():
    tree = ast.parse((COMP / "water_heater.py").read_text())
    tree.body = [node for node in tree.body if not isinstance(node, ast.ImportFrom)
                 or node.module == "__future__"]
    namespace = {
        "CoordinatorEntity": CoordinatorEntity, "WaterHeaterEntity": WaterHeaterEntity,
        "UnitOfTemperature": SimpleNamespace(CELSIUS="°C"), "DOMAIN": "mytesy",
        "device_family": FAMILIES["device_family"],
    }
    exec(compile(tree, str(COMP / "water_heater.py"), "exec"), namespace)
    return SimpleNamespace(**namespace)


WH = load_water_heater()


class ReadOnlyWaterHeaters(unittest.IsolatedAsyncioTestCase):
    def coordinator(self):
        return SimpleNamespace(data={
            "AA": {"device": {"model": "B15"}, "name": "Boiler", "state": {
                "current_temp": 42, "set_temp": 50, "mode": "man", "stand_by": "no"}},
            "BB": {"device": {"model": "E32"}, "state": {
                "heat_level": 3, "current_heat_level": 2, "mode": "p1", "stand_by": "no"}},
            "CC": {"device": {"model": "HPWH4_11"}, "state": {
                "current_temp": 45, "temp": 55, "mode": "hp", "power_status": "on"}},
            "DD": {"device": {"model": "cn06as"}, "state": {}},
        })

    async def test_all_three_families_remain_discoverable_without_controls(self):
        entities = []
        hass = SimpleNamespace(data={"mytesy": {"entry": {"coordinator": self.coordinator()}}})
        await WH.async_setup_entry(hass, SimpleNamespace(entry_id="entry"), entities.extend)
        self.assertEqual([entity._attr_unique_id for entity in entities], ["AA_water_heater", "BB_water_heater", "CC_water_heater"])
        for entity in entities:
            self.assertEqual(entity.supported_features, 0)
            for method in ("_send", "async_turn_on", "async_turn_off", "async_set_temperature", "async_set_operation_mode"):
                self.assertNotIn(method, WH.TesyWaterHeater.__dict__)

    async def test_temperatures_modes_and_attributes_still_update(self):
        coordinator = self.coordinator()
        b15, e32, hp = (WH.TesyWaterHeater(coordinator, mac) for mac in ("AA", "BB", "CC"))
        self.assertEqual((b15.native_current_temperature, b15.native_target_temperature, b15.current_operation), (42, 50, "man"))
        self.assertIsNone(e32.native_current_temperature)
        self.assertEqual(e32.extra_state_attributes["heat_level"], 3)
        self.assertEqual((hp.native_current_temperature, hp.native_target_temperature, hp.current_operation), (45, 55, "hp"))
        coordinator.data["AA"]["state"]["stand_by"] = "yes"
        coordinator.data["CC"]["state"]["power_status"] = "off"
        self.assertEqual(b15.current_operation, "off")
        self.assertEqual(hp.current_operation, "off")

    async def test_editable_calendars_are_created_only_for_convectors(self):
        tree = ast.parse((COMP / "calendar.py").read_text())
        setup = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef) and node.name == "async_setup_entry")
        namespace = {"DOMAIN": "mytesy", "supports_water_heater": FAMILIES["supports_water_heater"],
                     "TesyWeeklyCalendar": lambda coordinator, mac: mac}
        exec(compile(ast.Module(body=[setup], type_ignores=[]), "calendar_setup", "exec"), namespace)
        hass = SimpleNamespace(data={"mytesy": {"entry": {"coordinator": self.coordinator()}}})
        entities = []
        await namespace["async_setup_entry"](hass, SimpleNamespace(entry_id="entry"), entities.extend)
        self.assertEqual(entities, ["DD"])


if __name__ == "__main__":
    unittest.main()
