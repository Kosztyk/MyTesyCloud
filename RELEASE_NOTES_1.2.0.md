# v1.2.0 — MyTESY native statistics and advanced convector settings (preview)

> Historical release note: this describes the validation status at the original release date. For subsequent maintainer-reported CN06AS tests and current status, see [VALIDATION.md](VALIDATION.md) and [README.md](README.md).


- Preserve v1.1.6 original `*_energy_estimated` identity, cumulative logic, and persistence.
- Add optional daily native TESY power, temperature and state statistics (separate entities, never substituted for energy).
- Add model/state gated switches for adaptive start, antifrost, open window, child lock, UV and weekly-program toggle.
- Add comfort, eco and temperature correction number entities where reported by device.
- Existing cloud controls remain intact.

**Not yet supported:** Program editing/calendar, device groups, multi-model water heaters and heat pumps. Their protocol differences need real hardware verification before safe device control.

**Hardware confirmation update (2026-11-04):** The maintainer confirms testing these convector write controls successfully on two TESY CN06AS convectors running firmware 4.79. Statistics are separately cloud-derived. See [VALIDATION.md](VALIDATION.md).

- Add manual refresh buttons and validated-field experimental per-interval schedule services.
- Defer full group management, graphical chart cards, and non-convector device controls pending live API verification.
