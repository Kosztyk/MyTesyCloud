# MyTESY Cloud v1.1.6 — Energy dashboard compatibility

Restore the original `Energy (estimated)` cumulative energy sensor and its unique ID, `*_energy_estimated`. Retain `total_increasing` and restore the last Home Assistant state after restarting, without writing an initial zero. The separate rolling 30-day estimate is now `*_energy_rolling_30d`. No dashboard source replacement is required if the original entity ID is preserved.

**Migration warning:** Upgrades from the v1.0.0 `tesy_cloud` domain to newer `tesy` domain releases can affect Home Assistant entity registry identities. Recorder data is not migrated or recreated. Back up Home Assistant before upgrading.

**Sensor setup fix:** Removes an obsolete `TesyCloudTotalEnergySensor` constructor left in the v1.1.6 registration loop. Its undefined class prevented the entire sensor platform from setting up, causing all TESY sensors to appear unavailable. Added a registration regression test.
