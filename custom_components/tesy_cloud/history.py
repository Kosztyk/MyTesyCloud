"""Persistent 30-day history for TESY devices (integration-managed).

Stores intervals in Home Assistant .storage via hass.helpers.storage.Store so
history survives restarts and does not depend on Recorder retention.

Tracks:
- device "status" (on/off)
- device "heating" (on/off)

Intervals are stored per MAC as a list of [start_iso, end_iso] pairs.
If end_iso is None, interval is currently active.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .status import derived_power_on_raw, is_state_fresh, stale_active_state, stale_transition_time, state_on

STORAGE_VERSION = 1


def _utcnow() -> datetime:
    return dt_util.utcnow()


def _iso(dt: datetime) -> str:
    return dt_util.as_utc(dt).isoformat()


def _parse_ts(value: Any) -> datetime | None:
    """Parse TESY timestamps like 'YYYY-MM-DD HH:MM:SS'."""
    if not value:
        return None
    if isinstance(value, datetime):
        return dt_util.as_utc(value)
    if not isinstance(value, str):
        return None
    s = value.strip()
    try:
        dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        # treat as local time if naive
        return dt_util.as_utc(dt_util.as_local(dt))
    except Exception:
        pass
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)
        return dt_util.as_utc(dt)
    except Exception:
        return None



@dataclass
class _Track:
    current_on: bool = False
    since_iso: str | None = None
    intervals: list[list[str | None]] = field(default_factory=list)

    def normalize(self) -> None:
        self.intervals = [i for i in self.intervals if isinstance(i, list) and len(i) == 2]


def _parse_iso_utc(value: str | None) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _merge_intervals(intervals: list[list[str | None]]) -> list[list[str | None]]:
    parsed: list[tuple[datetime, datetime | None]] = []
    for item in intervals:
        if not isinstance(item, list) or len(item) != 2:
            continue
        start = _parse_iso_utc(item[0])
        end = _parse_iso_utc(item[1]) if item[1] else None
        if start is None:
            continue
        if end is not None and end < start:
            start, end = end, start
        parsed.append((start, end))

    parsed.sort(key=lambda x: x[0])
    merged: list[list[str | None]] = []
    for start, end in parsed:
        if not merged:
            merged.append([_iso(start), _iso(end) if end else None])
            continue

        last_start = _parse_iso_utc(merged[-1][0])
        last_end = _parse_iso_utc(merged[-1][1]) if merged[-1][1] else None
        if last_start is None:
            merged.append([_iso(start), _iso(end) if end else None])
            continue

        # open interval swallows all later intervals
        if last_end is None:
            continue

        overlaps = start <= last_end
        touches = (start - last_end).total_seconds() <= 1
        if overlaps or touches:
            if end is None or last_end is None:
                merged[-1][1] = None
            elif end > last_end:
                merged[-1][1] = _iso(end)
        else:
            merged.append([_iso(start), _iso(end) if end else None])
    return merged


class TesyHistoryManager:
    def __init__(self, hass: HomeAssistant, entry_id: str, keep_days: int = 30) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.keep_days = keep_days
        self._store = Store(hass, STORAGE_VERSION, f"{DOMAIN}_{entry_id}_history")
        self._data: dict[str, dict[str, _Track]] = {}
        self._loaded = False

    async def async_load(self) -> None:
        try:
            stored = await self._store.async_load()
        except Exception:
            stored = None
        self._data = {}
        if stored and isinstance(stored, dict):
            for mac, per in (stored.get("devices") or {}).items():
                if not isinstance(per, dict):
                    continue
                status = per.get("status") if isinstance(per.get("status"), dict) else {}
                heating = per.get("heating") if isinstance(per.get("heating"), dict) else {}
                self._data[mac] = {
                    "status": _Track(**status),
                    "heating": _Track(**heating),
                }
                self._data[mac]["status"].normalize()
                self._data[mac]["heating"].normalize()
                self._data[mac]["status"].intervals = _merge_intervals(self._data[mac]["status"].intervals)
                self._data[mac]["heating"].intervals = _merge_intervals(self._data[mac]["heating"].intervals)

        self._loaded = True
        self.prune_all(_utcnow())
        await self._save()

    async def _save(self) -> None:
        payload = {
            "devices": {
                mac: {
                    "status": {
                        "current_on": tr["status"].current_on,
                        "since_iso": tr["status"].since_iso,
                        "intervals": tr["status"].intervals,
                    },
                    "heating": {
                        "current_on": tr["heating"].current_on,
                        "since_iso": tr["heating"].since_iso,
                        "intervals": tr["heating"].intervals,
                    },
                }
                for mac, tr in self._data.items()
            }
        }
        await self._store.async_save(payload)

    def _ensure(self, mac: str) -> dict[str, _Track]:
        if mac not in self._data:
            self._data[mac] = {"status": _Track(), "heating": _Track()}
        return self._data[mac]

    def prune_all(self, now: datetime) -> None:
        cutoff = now - timedelta(days=self.keep_days + 2)  # small buffer
        cutoff_iso = _iso(cutoff)
        for mac in list(self._data.keys()):
            for key in ("status", "heating"):
                track = self._data[mac][key]
                pruned: list[list[str | None]] = []
                for start_iso, end_iso in track.intervals:
                    if end_iso is None or end_iso >= cutoff_iso:
                        pruned.append([start_iso, end_iso])
                track.intervals = _merge_intervals(pruned)

    def _apply_transition(self, track: _Track, new_on: bool, ts: datetime) -> bool:
        if new_on == track.current_on:
            return False
        ts_iso = _iso(ts)
        if new_on:
            track.current_on = True
            track.since_iso = ts_iso
            track.intervals.append([ts_iso, None])
        else:
            track.current_on = False
            if track.intervals and track.intervals[-1][1] is None:
                track.intervals[-1][1] = ts_iso
            else:
                track.intervals.append([ts_iso, ts_iso])
            track.since_iso = None
        return True

    async def process_snapshot(self, snapshot: dict[str, Any]) -> None:
        if not self._loaded:
            await self.async_load()

        now = _utcnow()
        changed = False

        for mac, payload in (snapshot or {}).items():
            if not isinstance(payload, dict):
                continue
            st = payload.get("state") or {}
            if not isinstance(st, dict):
                continue

            ts = _parse_ts(st.get("updated_at")) or now

            if stale_active_state(st, now):
                stale_at = stale_transition_time(st, now)
                ts = stale_at or now
                status_on = False
                heating_on = False
            else:
                status_on = derived_power_on_raw(st)
                heating_on = state_on(st.get("heating"))
                if heating_on:
                    status_on = True

            tracks = self._ensure(mac)
            if self._apply_transition(tracks["status"], status_on, ts):
                changed = True
            if self._apply_transition(tracks["heating"], heating_on, ts):
                changed = True

        self.prune_all(now)
        if changed:
            await self._save()

    def _duration_seconds_in_window(self, intervals: list[list[str | None]], now: datetime, days: int) -> float:
        window_start = now - timedelta(days=days)
        total = 0.0
        for start_iso, end_iso in intervals:
            try:
                start = datetime.fromisoformat(start_iso)
                if start.tzinfo is None:
                    start = start.replace(tzinfo=timezone.utc)
                end = datetime.fromisoformat(end_iso) if end_iso else now
                if end.tzinfo is None:
                    end = end.replace(tzinfo=timezone.utc)
            except Exception:
                continue

            if end < window_start:
                continue
            if start < window_start:
                start = window_start
            if end > now:
                end = now
            if end > start:
                total += (end - start).total_seconds()
        return total

    def get_hours_last_days(self, mac: str, key: str, days: int = 30) -> float:
        now = _utcnow()
        track = self._ensure(mac)[key]
        intervals = _merge_intervals(track.intervals)
        seconds = self._duration_seconds_in_window(intervals, now, days)
        max_seconds = float(days * 24 * 3600)
        seconds = max(0.0, min(seconds, max_seconds))
        return round(seconds / 3600.0, 3)

    async def async_reset(self, mac: str | None = None) -> None:
        if mac:
            self._data.pop(mac, None)
        else:
            self._data = {}
        await self._save()
