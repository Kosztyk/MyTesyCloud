# v1.2.3 feature build

- Native Home Assistant editable weekly calendar platform for TESY convectors using setProgram/deleteProgram.
- Native cloud device-group API create/edit/delete/add-device operations and a groups sensor.
- A dashboard YAML with native calendar and Recorder graphs.
- Preserves the existing energy sensor names and unique IDs.

Limitations: TESY's weekday numbering and optional device model capabilities require physical verification. This release does NOT claim water-heater or heat-pump control, nor an installed custom visual scheduler frontend. These devices have different API contracts; they cannot safely use the convector implementation. The graphical trend dashboard relies on HA's recorder history of the selected entities; its statistics endpoints remain separately exposed.
