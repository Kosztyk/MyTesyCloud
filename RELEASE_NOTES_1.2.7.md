# v1.2.7 — Schedule editor entity setup fix

Fix a Home Assistant platform error: configuration-category sensor entities are rejected. The Schedule editor remains a normal sensor with the same unique ID and device association. The dedicated TESY schedules panel remains available. Existing energy entities and their identities are unchanged.
