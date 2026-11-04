"""Native weekly TESY programming through the Home Assistant calendar UI."""
from __future__ import annotations
from datetime import datetime, timedelta
from uuid import uuid4
import logging
from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util
from homeassistant.exceptions import HomeAssistantError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def _program_items(raw):
    if isinstance(raw, list):
        return [v for v in raw if isinstance(v, dict)]
    if isinstance(raw, dict):
        if isinstance(raw.get("program"), (list, dict)):
            return _program_items(raw["program"])
        return [dict(v, program_number=v.get("program_number", key)) for key, v in raw.items() if isinstance(v, dict)]
    return []


def _as_weekday(day):
    # TESY cloud weekday numbering needs hardware validation, use documented ISO day 1-7 here.
    try:
        i = int(day)
        return i if 1 <= i <= 7 else None
    except (ValueError, TypeError):
        return None


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(TesyWeeklyCalendar(coordinator, mac) for mac in (coordinator.data or {}))


class TesyWeeklyCalendar(CoordinatorEntity, CalendarEntity):
    """Display/edit recurring intervals using HA's native calendar editor."""
    _attr_has_entity_name = True
    _attr_name = "Weekly Heating Program"

    def __init__(self, coordinator, mac):
        super().__init__(coordinator)
        self.mac = mac
        self._attr_unique_id = f"{mac}_weekly_calendar"
        self._attr_device_info = {"identifiers": {(DOMAIN, mac)}}

    def _intervals(self, start_date, end_date):
        state = (self.coordinator.data or {}).get(self.mac, {}).get("state") or {}
        items = _program_items(state.get("program"))
        tz = dt_util.get_time_zone(self.hass.config.time_zone)
        base = datetime.combine(start_date, datetime.min.time(), tzinfo=tz)
        result = []
        # Rolling weekly program; avoid allocating more than 70 days.
        for day_index in range(min((end_date-start_date).days + 1, 70)):
            date = (base + timedelta(days=day_index)).date()
            for item in items:
                if _as_weekday(item.get("day")) != date.isoweekday():
                    continue
                try:
                    hour1, min1 = [int(x) for x in str(item["from"]).split(":")[:2]]
                    hour2, min2 = [int(x) for x in str(item["to"]).split(":")[:2]]
                    start = datetime(date.year, date.month, date.day, hour1, min1, tzinfo=tz)
                    end = datetime(date.year, date.month, date.day, hour2, min2, tzinfo=tz)
                    if end <= start: end += timedelta(days=1)
                    result.append(CalendarEvent(start=start, end=end,
                        summary=f"Heat {item.get('temp', '?')}°C",
                        uid=str(item.get("program_number", "")),
                        description=f"TESY program #{item.get('program_number', '?')}"))
                except (ValueError, KeyError, TypeError):
                    _LOGGER.debug("Unrecognized TESY program interval for %s", self.mac)
        return result

    @property
    def event(self):
        now = dt_util.now()
        items = self._intervals(now.date(), (now + timedelta(days=8)).date())
        return next((e for e in sorted(items, key=lambda v:v.start) if e.end > now), None)

    async def async_get_events(self, hass, start_date, end_date):
        return [e for e in self._intervals(start_date.date(), end_date.date()) if e.end > start_date and e.start < end_date]

    async def async_create_event(self, **kwargs):
        start, end = kwargs.get("start"), kwargs.get("end")
        if not isinstance(start, datetime) or not isinstance(end, datetime) or end <= start or (end-start) > timedelta(days=1):
            raise HomeAssistantError("Use a timed interval within one day")
        summary = str(kwargs.get("summary") or "")
        import re
        match = re.search(r"(\d+(?:\.\d+)?)", summary)
        if not match:
            raise HomeAssistantError("Event title must contain target temperature, e.g. 'Heat 22°C'")
        temp = float(match.group(1))
        if not 5 <= temp <= 35:
            raise HomeAssistantError("Temperature must be between 5 and 35°C")
        state = (self.coordinator.data or {}).get(self.mac, {}).get("state") or {}
        used = {int(x.get("program_number")) for x in _program_items(state.get("program")) if str(x.get("program_number", "")).isdigit()}
        number = next((n for n in range(1, 256) if n not in used), None)
        if number is None: raise HomeAssistantError("No available TESY program slots")
        device = (self.coordinator.data or {}).get(self.mac, {})["device"]
        await self.coordinator.api.async_send_command(device, "setProgram", {
            "day": start.isoweekday(), "from": start.strftime("%H:%M"),
            "to": end.strftime("%H:%M"), "temp": int(round(temp)), "program_number": number})
        await self.coordinator.async_request_refresh()

    async def async_update_event(self, uid, event, recurrence_id=None, recurrence_range=None):
        """Edit a program from the HA calendar editor, retaining its slot number."""
        try: number = int(uid)
        except (ValueError, TypeError) as exc: raise HomeAssistantError("Invalid program number") from exc
        state = (self.coordinator.data or {}).get(self.mac, {}).get("state") or {}
        items = _program_items(state.get("program"))
        current = next((item for item in items if str(item.get("program_number")) == str(number)), None)
        if current is None: raise HomeAssistantError("TESY program no longer exists")
        start = event.get("start")
        end = event.get("end")
        if not isinstance(start, datetime) or not isinstance(end, datetime) or end <= start or end-start > timedelta(days=1):
            raise HomeAssistantError("Use a timed program interval within one day")
        import re
        summary = str(event.get("summary") or "")
        match = re.search(r"(\d+(?:\.\d+)?)", summary)
        temp = float(match.group(1)) if match else float(current.get("temp", 20))
        if not 5 <= temp <= 35: raise HomeAssistantError("Temperature must be between 5 and 35°C")
        device = (self.coordinator.data or {}).get(self.mac, {})["device"]
        await self.coordinator.api.async_send_command(device, "setProgram", {
            "day": start.isoweekday(), "from": start.strftime("%H:%M"),
            "to": end.strftime("%H:%M"), "temp": int(round(temp)), "program_number": number})
        await self.coordinator.async_request_refresh()

    async def async_delete_event(self, uid, recurrence_id=None, recurrence_range=None):
        try: number = int(uid)
        except (ValueError, TypeError) as exc: raise HomeAssistantError("Unrecognized TESY program ID") from exc
        items = _program_items(((self.coordinator.data or {}).get(self.mac, {}).get("state") or {}).get("program"))
        if not any(str(x.get("program_number")) == str(number) for x in items):
            raise HomeAssistantError("TESY program no longer exists; refresh calendar")
        device = (self.coordinator.data or {}).get(self.mac, {})["device"]
        await self.coordinator.api.async_send_command(device, "deleteProgram", {"program_number": number})
        await self.coordinator.async_request_refresh()
