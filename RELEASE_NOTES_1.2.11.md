# v1.2.11 — TESY schedule state and editor correction

- Removed redundant sidebar visibility information card from the schedule editor.
- Existing sidebar visibility switches remain separate from device programming.
- TESY `programStatus: null` is presented as *Status unavailable*, never *Off*.
- Missing program data is presented as *Schedule not reported*; editing is disabled to prevent accidental changes when the device schedule cannot be read.
- Weekly Program switch retains its unique ID but reports *Unavailable* when TESY does not supply `programStatus`. This avoids presenting an ambiguous `Unknown` toggle or orphaning the existing registry entry.
- Preserved all energy entities and history storage unchanged.

## Domain isolation for HACS catalog approval

The integration is now published under `mytesy` and installs exclusively into `custom_components/mytesy/`, eliminating a collision with the unrelated local TESY integration (`custom_components/tesy`). API, MQTT, device controls, energy unique IDs, and energy calculations are otherwise preserved.

**Manual migration from old `tesy` installs:** Back up Home Assistant, remove only the old *MyTESY Cloud* config entry and its `tesy` folder (never the unrelated local TESY integration), install `mytesy`, restart, and re-add your MyTESY Cloud account. The new domain/config entry may create different entity IDs and statistics IDs; Recorder data and integration-local energy history are not automatically migrated. See the README before updating production.
