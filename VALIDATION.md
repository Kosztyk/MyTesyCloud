# Validation notes

GitHub Actions runs HACS validation (without ignored checks), Home Assistant Hassfest, metadata checks and Python compilation.

```sh
python3 tools/check_repository.py
python3 -m unittest discover -s tests -v
python3 -m compileall -q custom_components
```

These tests are structural and do not authenticate to TESY services or exercise a physical heater. Device operations and historical Home Assistant configuration should be tested on a real installation before considering them verified.

A 9 MB standalone `tesy.js` reference bundle was moved to `reference/tesy.js` because it is not imported by the integration's Python modules.
