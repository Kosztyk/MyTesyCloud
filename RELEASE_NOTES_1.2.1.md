# v1.2.1 preview — guarded TESY cloud consumption source

Preserves the original `energy_estimated` sensor identity and Home Assistant energy history. Prefer explicitly cumulative TESY cloud kWh when available, with a migration offset. Never interpret empty response or periodic working-time as lifetime consumption. Fall back to the previously supported local energy estimate when cloud data is insufficient. Exposes `energy_source` attribute. This is experimental and needs a verified statistics response before cloud-derived consumption can be guaranteed.
