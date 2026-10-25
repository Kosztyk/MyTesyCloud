# Changelog

## Unreleased — Hardware validation and accurate documentation

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
