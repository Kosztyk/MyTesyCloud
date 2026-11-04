# MyTESY Cloud v1.2.5 - Schedule editor and login

> Historical release note: this describes the validation status at the original release date. For subsequent maintainer-reported CN06AS tests and current status, see [VALIDATION.md](VALIDATION.md) and [README.md](README.md).


- Added clickable **Schedule editor** sensor with `Open` state and built-in TESY weekly timetable editor.
- Added form controls for creating, modifying and deleting schedule slots; commands are sent through existing HA actions.
- New integrations accept e-mail/password without manually entering user ID; the app-user-login endpoint supplies it automatically.
- Existing config entries, legacy unique IDs and cumulative energy sensor semantics remain unchanged.
- **Hardware confirmation update (2026-11-04):** The maintainer confirms successful editing and deletion of schedules on TESY CN06AS convectors running firmware 4.79.
- The editor is available on the device through its Schedule editor sensor; requires HA frontend and admin access.
