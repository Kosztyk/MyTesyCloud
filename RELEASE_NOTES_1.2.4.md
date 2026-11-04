# v1.2.4 — water heater family integration

> Historical release note: this describes the validation status at the original release date. For subsequent maintainer-reported CN06AS tests and current status, see [VALIDATION.md](VALIDATION.md) and [README.md](README.md).


Added a Home Assistant water_heater platform for MyTESY APK B15, E32 and HPWH4_11 families, including family-specific power and mode controls. HPWH4_11 and B15 temperature setpoints use the official mobile app MQTT request payloads. E32 has heat-level control only and is **not** misrepresented as a temperature setpoint. Unknown models are intentionally left on the legacy integration path pending model identifiers. B15/E32/HPWH4_11 are distinct water-heater families; testing a CN06AS convector does not establish model-specific validation for these appliances. Convector energy unique IDs, their names, and stored data are untouched.
