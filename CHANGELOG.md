# Changelog

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
