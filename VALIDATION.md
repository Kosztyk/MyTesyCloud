# Validation notes

## Real-hardware validation

On 2026-10-25, the maintainer confirmed successful testing of the integration's
write controls on **two physical TESY Convector CN06AS heaters**. Both units
report **firmware 4.79**, verified through Home Assistant's device registry.

The maintainer has additionally confirmed that the available convector settings and weekly program editing/deleting commands were tested successfully on these two CN06AS devices, including `setAdaptiveStart`, `setAntiFrost`, `setOpenedWindow`, `setLockDevice`, `setUV`, `setProgramStatus`, `setComfortTemp`, `setEcoTemp`, `setTCorrection`, `setProgram` and `deleteProgram`. Existing controls remain writable.

Model-specific `powerOnOff`, `setStandby`, and `setMode` commands for B15, E32 and HPWH4_11 water heaters remain available; the cited CN06AS hardware does not establish validation for those separate appliance families. No model-specific water-heater hardware/firmware has been identified for the review record.


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
