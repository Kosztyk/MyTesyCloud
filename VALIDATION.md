# Validation notes

## v1.2.13 water-heater and HTTP error safeguards

B15, E32 and HPWH4_11 water-heater families have no physical model/firmware
confirmation. Their entities retain read-only observations with no supported
control features or write methods. The shared API rejects water-heater commands
before MQTT or app-log requests, and editable calendars/schedule links are not
created for these families. Controls may be enabled separately for a family
after a contributor validates its command payloads and resulting appliance
state on real hardware and supplies the model and firmware details.

Offline tests exercise HTTP 429/500/502/503 responses, transport failures,
timeouts and invalid JSON using credential-bearing exception URLs. They check
both error messages and formatted tracebacks for credential disclosure across
device, statistics, group and login requests. They also cover authentication
rejection, successful responses, app-log debug logging, water-heater discovery
and state reporting, blocked writes, and continued convector MQTT publishing.
No test contacts MyTESY or sends commands to a physical appliance.

The test suite requires `aiohttp` (also supplied by Home Assistant at runtime).
For a standalone checkout, install it with `python3 -m pip install aiohttp`
before running the commands below.

## Real-hardware validation

On 2026-10-25, the maintainer confirmed successful testing of the integration's
write controls on **two physical TESY Convector CN06AS heaters**. Both units
report **firmware 4.79**, verified through Home Assistant's device registry.

The maintainer has additionally confirmed that the available convector settings and weekly program editing/deleting commands were tested successfully on these two CN06AS devices, including `setAdaptiveStart`, `setAntiFrost`, `setOpenedWindow`, `setLockDevice`, `setUV`, `setProgramStatus`, `setComfortTemp`, `setEcoTemp`, `setTCorrection`, `setProgram` and `deleteProgram`. Existing controls remain writable.


## Automated validation

GitHub Actions runs HACS validation (without ignored checks), Home Assistant Hassfest, metadata checks and Python compilation.

```sh
python3 tools/check_repository.py
python3 -m unittest discover -s tests -v
python3 -m compileall -q custom_components
```

These automated tests are structural and do not authenticate to TESY services
or exercise a physical heater. They are separate from the successful
maintainer hardware tests documented above.

## Sensor documentation

The shipped sensor set has no device date/time sensor. The energy entity is a
regular rolling 30-day estimate, calculated from locally tracked heating hours
and the currently reported wattage. It is neither a cumulative total nor a
diagnostic entity. The README now describes that behavior and the two rolling
30-day runtime sensors.

## Reference material

A 9 MB standalone `tesy.js` reference bundle was moved to `reference/tesy.js` because it is not imported by the integration's Python modules.

## v1.1.6 legacy energy identity

Automated regression checks confirm the original energy unique ID, cumulative metadata, restore-state path and separate rolling sensor identity. Live-device and real-recorder upgrade verification is still required before publication.

## v1.2.11 domain conflict resolution

This release's Home Assistant domain is `mytesy`; there is no `custom_components/tesy` integration directory. All production service calls use `mytesy`, and frontend assets/routes are namespaced to `mytesy`. HACS/Hassfest, package and unit validation run on this layout. Previous `tesy` installations must be manually re-added; the rename alone does not migrate Recorder energy statistics.
