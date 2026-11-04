# v1.2.4 — water heater family integration

Added a Home Assistant water_heater platform for MyTESY APK B15, E32 and HPWH4_11 families, including family-specific power and mode controls. HPWH4_11 and B15 temperature setpoints use the official mobile app MQTT request payloads. E32 has heat-level control only and is **not** misrepresented as a temperature setpoint. Unknown models are intentionally left on the legacy integration path pending model identifiers. Real hardware validation is still required. Convector energy unique IDs, their names, and stored data are untouched.
