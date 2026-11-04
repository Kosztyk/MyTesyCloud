# Cloud energy-source status (experimental)

The entity `*_energy_estimated` (and its name) is unchanged. This build reads the TESY native power statistics coordinator and can use an **explicit lifetime cumulative kWh field** (`lifetime_energy_kwh` or `total_energy_kwh`) with a baseline offset to preserve the previous reading.

**Important:** The user’s actual TESY devices currently expose **zero power-statistics points** through the integration. In addition, the APK has `working_time`, but that field is period-based and its units/schema have not been verified live. We must not treat it as lifetime kWh. Until a verified cumulative value is returned, the sensor retains its local estimated calculation.

The sensor attribute `energy_source` reports `tesy_cloud_cumulative`, `tesy_cloud_cumulative_rebased`, or `local_fallback`. This is not a production promise that the installed TESY firmware supplies lifetime kWh.

A follow-up read-only capture of the raw `/get-device-power-stat` response (with personal information redacted) is required before we can map day/month `working_time` reliably. Do not overwrite Home Assistant historical statistics or reset the entity registry.
