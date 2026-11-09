# MyTESY Cloud v1.2.13

This release addresses the two remaining findings in HACS PR #12458.

- **Read-only water heaters:** B15, E32 and HPWH4_11 entities retain their state,
  temperatures and diagnostics, but advertise no supported control features and
  have no entity write methods. Their commands are also rejected in the shared
  API, so schedule services cannot bypass the restriction. Editable calendars
  and schedule-editor links are created only for convectors.
- **Community hardware validation:** The README announces that water-heater
  control can be enabled per family once a contributor validates the command
  payloads and resulting device state on real hardware with model and firmware
  details. No water-heater hardware confirmation is claimed.
- **Credential-safe errors:** HTTP response failures expose only the status,
  never the request URL. Transport/JSON failures suppress the original exception
  chain and omit response bodies across devices, statistics, groups and login.
  App-log debug output records the error type rather than its raw text.
- **Regression checks:** Add offline coverage of HTTP failures, formatted
  tracebacks, authentication rejection, successful responses, water-heater
  monitoring and blocked commands, plus confirmed convector command publishing.

The confirmed CN06AS convector controls, entity unique IDs and energy-history
calculations are preserved. Existing `mytesy` installations can upgrade in place
and restart Home Assistant. GitHub Actions runs packaging, unit tests, Python
compilation, HACS and Hassfest before publishing this release.
