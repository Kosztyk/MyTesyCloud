# MyTESY Cloud v1.1.3 — Hardware validation and documentation corrections

Addresses the remaining feedback in [HACS PR #12458](https://github.com/hacs/default/pull/12458).

- Records successful maintainer tests of power on/off (`onOff`), target temperature (`setTemp`) and mode/preset changes (`setMode`) on two physical TESY Convector CN06AS heaters. Both report firmware 4.79 in Home Assistant.
- Removes the outdated statement that device controls still require hardware verification, while keeping automated CI checks clearly separate from maintainer hardware testing.
- Removes the nonexistent date/time sensor from the README.
- Describes estimated energy as a regular rolling 30-day value based on heating hours and currently reported wattage, rather than a cumulative or diagnostic sensor. Documents both 30-day runtime sensors.
- Updates the config-flow text to describe monitoring and climate controls, with synchronized `strings.json` and `translations/en.json`.

This release changes documentation, setup text and release metadata. MQTT payloads, climate control, cloud authentication and sensor calculations are unchanged. The reported hardware validation applies to the two tested CN06AS units; it is not a claim about all TESY models or firmware versions.
