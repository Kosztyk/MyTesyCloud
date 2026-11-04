"""Shared TESY state freshness and derived-status helpers."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from homeassistant.util import dt as dt_util

from .const import TESY_STATE_STALE_MINUTES


STALE_DELTA = timedelta(minutes=TESY_STATE_STALE_MINUTES)


def state_on(v: Any) -> bool:
    if isinstance(v, str):
        return v.lower() == "on"
    if isinstance(v, bool):
        return v
    return False


def parse_updated_at(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        dt = datetime.strptime(value.strip(), "%Y-%m-%d %H:%M:%S")
        return dt_util.as_utc(dt_util.as_local(dt))
    except Exception:
        return None


def is_state_fresh(state: dict[str, Any], now: datetime | None = None) -> bool:
    updated_at = parse_updated_at(state.get("updated_at"))
    if updated_at is None:
        return False
    if now is None:
        now = dt_util.utcnow()
    return updated_at >= now - STALE_DELTA


def stale_transition_time(state: dict[str, Any], now: datetime | None = None) -> datetime | None:
    updated_at = parse_updated_at(state.get("updated_at"))
    if updated_at is None:
        return now or dt_util.utcnow()
    if now is None:
        now = dt_util.utcnow()
    cutoff = updated_at + STALE_DELTA
    return cutoff if cutoff < now else None


def derived_power_on_raw(state: dict[str, Any]) -> bool:
    """Resolve power from the explicit status; heating describes action, not mode."""
    reported_status = state.get("status")
    if isinstance(reported_status, bool):
        return reported_status
    if isinstance(reported_status, str) and reported_status.lower() in ("on", "off"):
        return reported_status.lower() == "on"
    return state_on(state.get("heating"))


def stale_active_state(state: dict[str, Any], now: datetime | None = None) -> bool:
    """Return True only when stale data still claims active heating.

    We can detect an unplugged heater reliably when the last cloud state said it
    was *heating* and then updates stop. We deliberately do *not* use preset mode
    or idle/powered state here, because Tesy often keeps those stale while the
    device is still online.
    """
    return (not is_state_fresh(state, now=now)) and state_on(state.get("heating"))


def derived_power_on(state: dict[str, Any], now: datetime | None = None) -> bool:
    """Stale cloud observations must not change the reported HVAC mode to Off."""
    return derived_power_on_raw(state)


def heating_active(state: dict[str, Any], now: datetime | None = None) -> bool:
    """Current heating action, separate from reported power state."""
    return derived_power_on_raw(state) and state_on(state.get("heating"))


def cloud_connected(device: dict[str, Any], state: dict[str, Any], now: datetime | None = None) -> bool:
    """Best-effort connectivity.

    - Fresh state updates mean connected.
    - Stale *active* state strongly suggests the heater disappeared mid-run.
    - Stale idle/off state is ambiguous with Tesy, so keep it connected/available
      instead of falsely marking healthy idle devices offline.
    """
    if is_state_fresh(state, now=now):
        return True
    if stale_active_state(state, now=now):
        return False
    return True
