# MyTESY Cloud v1.2.12 — HACS review corrections

1. Record the maintainer's confirmation of physical CN06AS (firmware 4.79) write-command tests for convector settings and weekly programs; retain all existing UI controls and write paths.
2. Fix `KeyError` from `_editor` and multi-account service routing: register services at setup; resolve correct loaded entry on every call; remove services and unregister the schedule panel on final unload.
3. Raise `ConfigEntryAuthFailed` on invalid credentials, supply reauthentication and replace the password without losing an existing config entry/entity identity. Network/server errors continue to be treated as transient.
4. Bump version and frontend asset URLs for cache refresh. Energy unique IDs and calculations are untouched.

GitHub Actions runs HACS, Hassfest, unit tests, and package validation before the automated release.
