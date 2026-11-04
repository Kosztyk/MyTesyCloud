## v1.2.11 — TESY schedules, cloud features and unique `mytesy` domain

A dedicated switch on every convector device controls only whether **TESY schedules** is shown in Home Assistant’s left navigation. It does not modify the heater weekly program. Sidebar visibility is saved and survives Home Assistant restarts. The mistaken schedule on/off switch inside the editor has been removed. Existing entities and energy sensor unique IDs are unchanged.


<img width="1200" height="630" alt="mytesy" src="https://github.com/user-attachments/assets/b830e541-2b22-44d6-8575-e99e18ba18ca" />


# MyTESY Cloud Convector (Home Assistant)

Unofficial Home Assistant custom integration for TESY MyTESY cloud appliances, primarily **convectors**, using the MyTESY **v4** cloud endpoint. Additional water-heater and heat-pump support is model-dependent and requires real-device validation.

This integration uses **cloud polling** for status and MQTT-over-WebSocket for power, temperature and preset commands. Sensors and binary sensors are read-only.

## Tested hardware

The maintainer has successfully tested the integration's write controls on
**two physical TESY Convector CN06AS heaters**. Both devices report
**firmware 4.79** in Home Assistant.

| Control tested on both heaters | MQTT command | Result |
| --- | --- | --- |
| Power on/off | `onOff` | Successful on real hardware |
| Target temperature changes | `setTemp` | Successful on real hardware |
| Mode/preset changes | `setMode` | Successful on real hardware |

This confirmation was provided by the maintainer on 2026-10-25; the firmware
versions were checked in the Home Assistant device registry. It applies to
these two CN06AS units and does not establish compatibility with every TESY
model or firmware. See [VALIDATION.md](VALIDATION.md) for the separate scope
of hardware testing and automated checks.

## Features

Per device (per MAC address), the integration creates:

- **Climate entity** (controllable: on/off, target temperature and comfort/eco/sleep presets)
  - Current temperature (`state.current_temp`)
  - Target temperature / setpoint (`state.temp`)
  - HVAC mode derived from `state.status` and `state.heating`, with stale active-state handling
  - HVAC action (`heating`/`idle`/`off`) derived from the power state and `state.heating`

- **Sensors** (read-only)
  - Heater power (`state.watt`)
  - Mode (`state.mode`)
  - Program status (`state.programStatus`)
  - Time remaining (minutes) (`state.timeRemaining`)
  - Mode time (minutes) (`state.modeTime`)
  - Temperature correction (`state.TCorrection`)
  - Comfort temperature (`state.comfortTemp.temp`)
  - Eco temperature (`state.ecoTemp.temp`)
  - Eco time (minutes) (`state.ecoTemp.time`)
  - Sleep time (minutes) (`state.sleepMode.time`)
  - Delayed start time (minutes) (`state.delayedStart.time`)
  - Delayed start temperature (`state.delayedStart.temp`)
  - Firmware version (diagnostic)
  - Wi‑Fi SSID (diagnostic)
  - Reported WAN IP (diagnostic)
  - Device timezone (diagnostic)
  - **Energy (estimated)** (kWh): original cumulative `total_increasing` sensor with stable `<MAC>_energy_estimated` unique ID; preserves the per-device estimate where the original entity can be restored. It is not a calibrated meter.
  - **Energy (estimated, last 30 days)** (kWh): separate informational rolling estimate which can decrease as older history leaves its window.
  - Native cloud power/temperature/state statistics and device profile sensors where supported; not guaranteed to return complete historical data.
  - **Power On Time (last 30 days)** (hours; regular sensor)
  - **Heating Time (last 30 days)** (hours; regular sensor)

- **Binary sensors** (read-only)
  - Device on (derived from `state.status` and `state.heating`, with stale active-state handling)
  - Heating active (`state.heating`, with stale active-state handling)
  - Open window detected (`state.openedWindow`)
  - Anti‑frost enabled (`state.antiFrost`)
  - Device locked (`state.lockedDevice`)
  - UV enabled (`state.uv`)
  - Adaptive start enabled (`state.adaptiveStart`)
  - Has internet (diagnostic; inferred from cloud-state freshness and idle presence, with the raw `hasInternet` value exposed as an attribute)
  - Waiting for connection (diagnostic) (`waitingForConnection`)

## Requirements

- A working MyTESY account and devices already added in the MyTESY app/portal.
- Home Assistant with support for custom components.
- Internet access from Home Assistant to the MyTESY endpoint (currently uses `https://ad.mytesy.com/rest/get-my-devices`).

## HACS installation

Before the integration is included in the default HACS catalog, open **HACS → Custom repositories**, add `https://github.com/Kosztyk/MyTesyCloud`, select **Integration**, install **MyTESY Cloud Convector**, and restart Home Assistant.

After the catalog submission is accepted, the custom-repository step will not be necessary.

## Installation

1. Copy the `mytesy` integration folder into Home Assistant:

   - Target path: `/config/custom_components/mytesy/`
   - You should have files like:
     - `/config/custom_components/mytesy/manifest.json`
     - `/config/custom_components/mytesy/__init__.py`
     - `/config/custom_components/mytesy/api.py`
     - `/config/custom_components/mytesy/climate.py`
     - `/config/custom_components/mytesy/sensor.py`
     - `/config/custom_components/mytesy/binary_sensor.py`

2. Restart Home Assistant.

**Important: migration from the previous `tesy` integration domain.**

This release uses the unique Home Assistant domain **`mytesy`**, avoiding a collision with the separate local TESY integration [`krasnoukhov/homeassistant-tesy`](https://github.com/krasnoukhov/homeassistant-tesy). Because Home Assistant identifies integrations by domain, upgrading an old `tesy` configuration entry in place **is not supported**. Follow these steps:

1. **Back up Home Assistant before making changes.** Record your existing entity IDs, Energy dashboard selections, utility meters, automation references and statistics. Back up your `.storage` history if energy continuity matters.
2. In **Settings → Devices & services**, remove only your *previous MyTESY Cloud* config entry under the old domain. Do not remove the separate local TESY integration if you use it.
3. If the old `/config/custom_components/tesy/` directory contains **this cloud project**, remove the old directory (after backing it up). If it belongs to the separate local TESY integration, **leave it intact**. Remove obsolete `/config/custom_components/tesy_cloud/` copies of this project if present.
4. Install the new `/config/custom_components/mytesy/` directory, restart Home Assistant and **Add integration → MyTESY Cloud** using your existing account credentials. You can omit the user ID if TESY login returns it automatically.
5. Review created entity IDs and reconnect dashboards, automations and Energy dashboard sources as needed. Entity IDs, Recorder statistics IDs and integration-local energy-history storage **may not be carried over** to the new domain/config entry. This build does not silently rewrite old statistics or guarantee an energy-history migration. Retain backups and historical Recorder data until you verify the new entities.

You can install both unrelated integrations together afterward: `custom_components/tesy` for local TESY water heaters and `custom_components/mytesy` for this cloud integration.

## Setup (UI)

1. Go to:
   - **Settings → Devices & Services → Add Integration**
2. Search for:
   - **MyTESY Cloud**
3. Fill in:
   - **E-mail**: your MyTESY login
   - **Password**: your MyTESY password
   - **User ID**: see the section below

After submitting, Home Assistant will create entities for each device returned by the MyTESY API.

## How to obtain the `user_id` from `https://v4.mytesy.com/`

MyTESY v4 uses the `userID` query parameter in its API calls. The most reliable way to get it is via your browser’s Developer Tools:

1. Open the portal in your browser: `https://v4.mytesy.com/`
2. Log in with your MyTESY account.
3. Open Developer Tools:
   - Chrome/Edge: `F12` → **Network**
   - Firefox: `F12` → **Network**
4. In **Network**, use the filter box and type:
   - `get-my-devices`
   - or `ad.mytesy.com`
5. Reload the page (or navigate to the dashboard) so the request appears.
6. Click the request that looks like:
   - `.../rest/get-my-devices?...`
7. In the request details, find **Query String Parameters** and copy:
   - `userID=<THIS VALUE>`

That value is what Home Assistant expects as **User ID** in the config flow.

<img width="1339" height="617" alt="Screenshot 2026-01-10 at 22 23 12" src="https://github.com/user-attachments/assets/8802a52f-ed13-494e-bba0-d107d2daaa50" />


Tip: If you don’t see anything in Network, ensure “Preserve log” is enabled and reload once.

## Troubleshooting

- **Auth failed / error=1**
  - One of: `user_id`, `username`, `password` is wrong.
  - Re-check the `userID` value from the v4 portal and retry.

- **No devices returned**
  - Confirm your devices appear in the MyTESY app/portal first.
  - Confirm Home Assistant can reach `ad.mytesy.com` over HTTPS.

- **Setup fails after updating files**
  - Restart Home Assistant fully (not only “Reload”).
  - If the integration changed platforms, removing and re-adding the integration can help.

## Security notes

- Your credentials are stored in the Home Assistant config entry.
- Consider restricting Home Assistant backups and access to your configuration.

## Disclaimer

This is an **unofficial** integration and is not affiliated with TESY.
API behavior may change without notice.

## Publication validation

HACS, Hassfest and packaging checks are run by GitHub Actions. These do not test commands against a live TESY device. See [VALIDATION.md](VALIDATION.md).

## License

[MIT License](LICENSE.txt); [original Romanian translation](docs/licenta-originala-ro.md).


## Scheduler, settings and appliance support in v1.2.11

- A **TESY schedules** custom panel is available at `/mytesy-schedules`, accessible using a Schedule editor sensor or the administrator sidebar. Its visibility is controlled by the **Show TESY schedules in sidebar** switch on a TESY convector; this affects navigation only, never heater programming.
- Weekly Program is a separate device setting. When TESY returns `programStatus: null`, the switch is **Unavailable** and the schedule panel reports **Status unavailable**. The panel does not treat missing program data as an empty schedule and disables editing until program data is reported.
- Cloud statistics, device profile/program diagnostics, convector settings, calendar, group-management services, and model-dependent water-heater and heat-pump entities are included in the source. Controls for appliance families and schedule interval writes are **not validated on all physical devices**. Consult the release notes and verify model-specific behavior before operating physical equipment.
- Service calls for schedule editing and group management now use the **`mytesy`** domain. There is no migration path that silently renames existing Home Assistant scripts or automations referring to old `tesy` services; update those manually.

## Estimated energy compatibility and domain migration

The original cumulative **Energy (estimated)** sensor retains its original unique ID (`<MAC>_energy_estimated`), `total_increasing` state class, and calculation logic. The separate 30-day rolling estimate is informational only. Cloud-derived estimates are used only when a usable cumulative cloud series is available; missing cloud data falls back to the local estimate.

**Warning:** The mandatory integration-domain rename from `tesy` to `mytesy` changes how Home Assistant associates config entries, devices, and entity registry entries. Identical per-device unique-ID suffixes **do not guarantee retention of the original entity IDs, Recorder statistics IDs or persisted integration history** when you remove and re-add the integration. A full Home Assistant backup and manual Energy dashboard/automation review are essential before migrating. This release does not automatically merge old entity history into the new domain.
