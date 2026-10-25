
<img width="1200" height="630" alt="mytesy" src="https://github.com/user-attachments/assets/b830e541-2b22-44d6-8575-e99e18ba18ca" />


# MyTESY Cloud Convector (Home Assistant)

Unofficial Home Assistant custom integration for TESY MyTESY (TESY Cloud) **convectors** using the MyTESY **v4** cloud endpoint.

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
  - **Energy (estimated, last 30 days)** (kWh; regular sensor)
    - Calculated as locally tracked heating hours over the last 30 days multiplied by the currently reported `state.watt` divided by 1000.
    - This rolling estimate can decrease as older heating history leaves the window, or change when the reported wattage changes. It is not a cumulative energy counter or a calibrated meter reading.
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

1. Copy the `tesy` integration folder into Home Assistant:

   - Target path: `/config/custom_components/tesy/`
   - You should have files like:
     - `/config/custom_components/tesy/manifest.json`
     - `/config/custom_components/tesy/__init__.py`
     - `/config/custom_components/tesy/api.py`
     - `/config/custom_components/tesy/climate.py`
     - `/config/custom_components/tesy/sensor.py`
     - `/config/custom_components/tesy/binary_sensor.py`

2. Restart Home Assistant.

**Important when upgrading an existing manual installation:** the old folder name `custom_components/tesy_cloud` did not match the integration domain `tesy`. Remove the obsolete `tesy_cloud` folder, install the new `tesy` folder and restart Home Assistant. The Home Assistant integration domain remains `tesy`, so existing configuration entries are intended to remain usable.

## Setup (UI)

1. Go to:
   - **Settings → Devices & Services → Add Integration**
2. Search for:
   - **MyTESY Cloud Convector**
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
