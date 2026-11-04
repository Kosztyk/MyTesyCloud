"""Model-family routing from the MyTESY 3.0 Android application."""

def device_family(device):
    model = str(device.get("model") or "").upper().replace("-", "_")
    # Restrict recognition to models whose command contracts are in APK source maps.
    if model.startswith("HPWH4_11_") or model == "HPWH4_11":
        return "heat_pump"
    if model == "B15" or model.startswith("B15_"):
        return "boiler_b15"
    if model == "E32" or model.startswith("E32_"):
        return "boiler_e32"
    if any(x in model for x in ("HPWH", "HEATPUMP", "BELLISLIMO", "BOILER", "AQUATHERM")):
        return "unsupported_water_heater"
    return "convector"

def supports_water_heater(device):
    return device_family(device) != "convector"
