# MyTESY Cloud v1.2.5 - Schedule editor and login

- Added clickable **Schedule editor** sensor with `Open` state and built-in TESY weekly timetable editor.
- Added form controls for creating, modifying and deleting schedule slots; commands are sent through existing HA actions.
- New integrations accept e-mail/password without manually entering user ID; the app-user-login endpoint supplies it automatically.
- Existing config entries, legacy unique IDs and cumulative energy sensor semantics remain unchanged.
- The TESY weekday and schedule command formats still require live device confirmation; changing an interval could affect heater programming.
- The editor is available on the device through its Schedule editor sensor; requires HA frontend and admin access.
