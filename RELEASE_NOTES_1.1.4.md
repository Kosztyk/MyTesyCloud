# MyTESY Cloud v1.1.4

Fixes a regression introduced after v1.0.0 where the Home Assistant thermostat card could unexpectedly show **Off** during a heating cycle when a TESY cloud update was stale.

- A stale `updated_at` no longer forces the climate entity into Off.
- The explicit TESY power `status` has priority over the `heating` activity flag.
- Heating versus idle action remains distinct from Heat versus Off mode.
- Adds targeted automated regression coverage.
- Maintainer and affected user report successful device testing; compatibility claims remain limited to the devices actually tested.

Existing MQTT commands, authentication, controls, sensors and entities remain unchanged.

## Validation

HACS, Hassfest, repository packaging checks, Python unit tests, and compilation must complete successfully on the release commit. Device testing was reported separately by the maintainer and user.
