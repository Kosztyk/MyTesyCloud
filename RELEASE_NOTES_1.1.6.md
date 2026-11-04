# MyTESY Cloud v1.1.6 — Unique integration domain

Addresses HACS PR #12458 by changing the domain and folder from `tesy` to `mytesy`, avoiding a collision with the unrelated local TESY water-heater integration.

All existing cloud API operations, MQTT commands, heater controls and sensor calculations remain unchanged.

**Manual upgrade required:** Back up Home Assistant, remove only the old MyTESY Cloud integration entry, install `custom_components/mytesy`, restart, and add MyTESY Cloud again. Remove `custom_components/tesy` only if it is the old cloud integration; leave it intact if used by the unrelated local TESY integration. Entity IDs and energy history may not migrate automatically. Review existing dashboard, automation and Energy dashboard references.
