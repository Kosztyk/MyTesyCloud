# v1.2.0 — MyTESY native statistics and advanced convector settings (preview)

- Preserve v1.1.6 original `*_energy_estimated` identity, cumulative logic, and persistence.
- Add optional daily native TESY power, temperature and state statistics (separate entities, never substituted for energy).
- Add model/state gated switches for adaptive start, antifrost, open window, child lock, UV and weekly-program toggle.
- Add comfort, eco and temperature correction number entities where reported by device.
- Existing cloud controls remain intact.

**Not yet supported:** Program editing/calendar, device groups, multi-model water heaters and heat pumps. Their protocol differences need real hardware verification before safe device control.

**Caution:** These new write controls have not been tested on physical TESY hardware. Native stats request payload formats must also be validated against live responses.

- Add manual refresh buttons and validated-field experimental per-interval schedule services.
- Defer full group management, graphical chart cards, and non-convector device controls pending live API verification.
