# MyTESY Cloud v1.1.2 — HACS review translation fix

This release resolves the missing Home Assistant English fallback from [HACS PR #12458](https://github.com/hacs/default/pull/12458).

- Add `custom_components/tesy/translations/en.json` with the exact contents of `strings.json`.
- Restore runtime config flow titles, field labels, and errors for languages without their own translation.
- Validate the fallback exists and matches in packaging checks.

No changes to cloud authentication, MQTT, device control, or sensors.
