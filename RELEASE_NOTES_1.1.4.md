# MyTESY Cloud v1.1.4 — Climate heating-state fix

Fixes a regression where Home Assistant could show the TESY climate entity as Off during heating when the latest cloud status timestamp was stale. Climate HVAC mode now follows the reported device power status rather than using stale state as evidence of an off command.

## Changes
- Restore stable Heat/Off state display for devices with old cloud timestamps.
- Report idle heater as Heat (idle), not Off, when TESY says the heater is powered on.
- Respect explicitly reported device Off status even if the heating flag is contradictory.
- Add regression tests for these states.

## Testing
Code-level regression tests and packaging checks; live hardware verification remains pending.
