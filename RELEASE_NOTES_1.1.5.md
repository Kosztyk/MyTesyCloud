# MyTESY Cloud v1.1.5 — Energy statistics correction

- Keep the original rolling 30-day kWh estimate, but remove its `measurement` state class because rolling windows can decrease.
- Add `Energy Total (estimated)` with `total_increasing` statistics and a stable unique ID.
- Persist cumulative estimated consumption in integration-managed Home Assistant storage, surviving restarts.
- Integrate only short observed intervals (maximum 120 seconds) to avoid counting long outages as consumption.
- Reset-history service also resets cumulative energy, which starts a new Home Assistant statistics cycle.

**Note:** Values are estimates based on the TESY heating flag and reported wattage, not measurements. The cumulative counter begins at zero on first use of v1.1.5; it cannot recover historical consumption that was not measured.
