"""TESY convector numeric settings verified against app command fields."""
from __future__ import annotations
from homeassistant.components.number import NumberEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfTemperature
from homeassistant.exceptions import HomeAssistantError
from .const import DOMAIN
from .device_families import supports_water_heater
FIELDS = {"comfortTemp": ("Comfort Temperature Setpoint", "setComfortTemp", 5, 35),
          "ecoTemp": ("Eco Temperature Setpoint", "setEcoTemp", 5, 35),
          "TCorrection": ("Temperature Correction Setting", "setTCorrection", -10, 10)}

async def async_setup_entry(hass, entry, async_add_entities):
    c=hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities=[]
    for mac, payload in (c.data or {}).items():
        if supports_water_heater(payload.get("device") or {}): continue
        st=payload.get("state") or {}
        for field in FIELDS:
            obj=st.get(field)
            val=obj.get("temp") if isinstance(obj,dict) else obj
            if isinstance(val, (int,float)) and not isinstance(val,bool):
                entities.append(TesySettingNumber(c,mac,field))
    async_add_entities(entities)

class TesySettingNumber(CoordinatorEntity, NumberEntity):
    _attr_native_step=1
    _attr_native_unit_of_measurement=UnitOfTemperature.CELSIUS
    def __init__(self, coordinator, mac, field):
        super().__init__(coordinator)
        self.mac,self.field=mac,field
        name, command, low,high = FIELDS[field]
        self._attr_native_min_value=low
        self._attr_native_max_value=high
        self._attr_name=f"{(coordinator.data or {}).get(mac, {}).get('name', 'TESY')} {name}"
        self._attr_unique_id=f"{mac}_setting_{field}"
        self._attr_device_info={"identifiers": {(DOMAIN,mac)}}
    @property
    def native_value(self):
        st=(self.coordinator.data or {}).get(self.mac,{}).get("state") or {}
        obj=st.get(self.field)
        return obj.get("temp") if isinstance(obj,dict) else obj
    async def async_set_native_value(self,value):
        payload=(self.coordinator.data or {}).get(self.mac,{})
        st=payload.get("state") or {}
        # ECO retains existing duration, as required by mobile-app setEcoTemp payload.
        params={"temp":int(value)}
        if self.field=="ecoTemp":
            eco=st.get("ecoTemp") or {}
            if not isinstance(eco,dict) or eco.get("time") is None:
                raise HomeAssistantError("Cannot change ECO temperature without its existing duration")
            params["time"]=eco["time"]
        try:
            await self.coordinator.api.async_send_command(payload.get("device") or {},FIELDS[self.field][1],params)
            await self.coordinator.async_request_refresh()
        except Exception as exc:
            raise HomeAssistantError("TESY setting update failed") from exc
