# Validation notes

## Real-hardware validation

On 2026-10-25, the maintainer confirmed successful testing of the integration's
write controls on **two physical TESY Convector CN06AS heaters**. Both units
report **firmware 4.79**, verified through Home Assistant's device registry.

The confirmed operations on both heaters are:

- Power on and off (`onOff`).
- Target temperature changes (`setTemp`).
- Mode/preset changes (`setMode`).

These are maintainer-reported results from real devices. The controls are
retained on that basis. This does not claim testing of every possible setting,
other TESY models, or other firmware versions. These corrections update
documentation and config-flow wording; they do not change MQTT payloads,
climate control methods, cloud authentication, or sensor calculations.

## v1.1.4 field validation

The maintainer and reporting user confirm successful operation of the v1.1.4 heating-state fix on their tested devices. The additional confirmation addresses the erroneous Heat-to-Off transition in the Home Assistant climate card. It does not imply universal testing across all TESY models or firmware versions. Existing CN06AS firmware 4.79 control testing remains documented above.

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
