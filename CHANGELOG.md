## 1.2.11 — Unique `mytesy` domain and schedule corrections

- Install exclusively in `custom_components/mytesy`; all integration services, scheduler frontend URLs, entity registration and tests use domain `mytesy`.
- Document the required re-add for existing `tesy` installations.

- Correct missing TESY program state handling and simplify schedule editor UI.

## v1.2.10 — TESY schedules sidebar visibility

A dedicated switch on every convector device controls only whether **TESY schedules** is shown in Home Assistant’s left navigation. It does not modify the heater weekly program. Sidebar visibility is saved and survives Home Assistant restarts. The mistaken schedule on/off switch inside the editor has been removed. Existing entities and energy sensor unique IDs are unchanged.

## 1.2.9
- Left-panel schedule enable/disable switch using Home Assistant switch service, with cloud-state feedback.
- Ensure weekly program switch exists even when programStatus is initially null.

## 1.2.7 — Schedule editor sensor setup fix
- Remove invalid CONFIG category from the Schedule editor sensor to restore its availability.
- Preserve schedule editor and energy sensor unique IDs.

## 1.2.6
- Place Schedule editor in the HA Configuration category and show the TESY schedules sidebar panel. Preserve entity identity.

## 1.2.2-preview — read-only device and program inspection

- Add program snapshot diagnostic sensor and model profile diagnostic sensor.
- Preserve existing cumulative energy entity names, IDs and estimated semantics.
- Document unimplemented full scheduling/editor, groups and non-convector control.

# Changelog

## 1.2.0 — TESY cloud statistics and settings preview

# v1.2.0 — MyTESY native statistics and advanced convector settings (preview)

- Preserve v1.1.6 original `*_energy_estimated` identity, cumulative logic, and persistence.
- Add optional daily native TESY power, temperature and state statistics (separate entities, never substituted for energy).
- Add model/state gated switches for adaptive start, antifrost, open window, child lock, UV and weekly-program toggle.
- Add comfort, eco and temperature correction number entities where reported by device.
- Existing cloud controls remain intact.

**Not yet supported:** Program editing/calendar, device groups, multi-model water heaters and heat pumps. Their protocol differences need real hardware verification before safe device control.

**Caution:** These new write controls have not been tested on physical TESY hardware. Native stats request payload formats must also be validated against live responses.



## 1.1.6 — Restore original energy sensor identity

- Restore the original cumulative Energy (estimated) unique ID, display name, total_increasing metadata, and RestoreEntity behavior.
- Move rolling 30-day estimate to a separate sensor with a new unique ID.
- Keep climate-state and history fixes from recent versions.
- Document entity registry and domain migration limitations.

## 1.1.5 — Energy statistics correction

- Preserve the rolling 30-day estimate as informational, without energy measurement state class.
- Add a persisted cumulative estimated energy sensor with total_increasing statistics.
- Avoid estimating consumption across long cloud polling gaps.
- Add coverage of accumulation, restart persistence, reset and metadata.


## 1.1.4 — Climate heating-state regression fix

- Keep Home Assistant climate mode on HEAT when TESY reports the device powered on, even if the cloud state timestamp is old.
- Separate device power mode from heating-element activity; idle heating must not be interpreted as switched off.
- Prefer explicit device `status` over contradictory `heating` state.
- Add focused regression tests for stale state, idle, off, and missing status.
- No changes to cloud authentication, device commands, or entity identifiers.


## 1.1.3 — Hardware validation and accurate documentation

- Document maintainer-confirmed power, temperature and mode control tests on two TESY CN06AS heaters, both reporting firmware 4.79.
- Separate successful real-hardware validation from the scope of automated checks.
- Remove the nonexistent date/time sensor from the README.
- Describe energy as a regular rolling 30-day estimate and include both runtime sensors.
- Correct the config-flow description in `strings.json` and `translations/en.json` to reflect climate controls.
- No runtime protocol, control or sensor changes.

## 1.1.2 — English fallback translation fix

- Add `translations/en.json` matching `strings.json` as Frenck requested in HACS #12458.
- Require and verify English translation in automated packaging checks.
- No runtime protocol, control or sensor changes.

## 1.1.1 — HACS publishing readiness

- Correct the component installation folder to `custom_components/tesy`, matching the existing Home Assistant domain `tesy`.
- Add HACS and Hassfest validation workflows and release automation.
- Add HACS metadata, maintainer and issue tracker details.
- Correct README's obsolete read-only description and installation paths.
- Preserve the original Romanian MIT translation under docs while making GitHub recognise the standard MIT license.
- Move the 9 MB bundled JavaScript reference file outside the installable integration.

TESY authentication, climate control, MQTT protocol and sensor implementations are unchanged.

## 1.2.5
- Built-in TESY visual weekly timetable via clickable Schedule editor sensor.
- Auto-discover userID from MyTESY login for newly configured installations.
