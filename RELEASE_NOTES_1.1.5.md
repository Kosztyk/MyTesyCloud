# MyTESY Cloud v1.1.5 — Energy statistics correction

- Retain original rolling 30-day kWh estimate without incompatible `measurement` state class.
- Add `Energy Total (estimated)` with `total_increasing` statistics and stable unique ID.
- Persist cumulative estimated consumption across restarts.
- Limit counted gaps between cloud observations to at most 120 seconds.
- Reset-history service also resets cumulative estimated energy.
- Add energy regression tests and Energy dashboard migration instructions.

**Upgrade action:** The old `*_energy_estimated` entities previously selected in Energy dashboard must be manually replaced with new `*_energy_total_estimated` entities. The integration cannot automatically update the Energy dashboard configuration.

These are estimated values from heating status and reported wattage, not calibrated meter readings. Cumulative energy begins at zero on initial installation of v1.1.5.
