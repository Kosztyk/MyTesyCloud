"""TESY schedules frontend and persistent, user-controlled sidebar visibility."""
from pathlib import Path
from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.helpers.storage import Store
from .const import DOMAIN

PANEL_PATH = "mytesy-schedules"
PANEL_NAME = "mytesy-schedule-panel-1-2-12"
EDITOR_ASSET = "/mytesy/schedule-editor-1.2.12.js"
ENTITY_ASSET = "/mytesy/schedule-entity-1.2.12.js"

async def async_sidebar_state(hass):
    state = hass.data.setdefault(DOMAIN, {}).setdefault("_editor", {})
    if "visible" not in state:
        saved = await Store(hass, 1, "mytesy_schedule_sidebar_visibility").async_load()
        if saved is None:
            saved = await Store(hass, 1, "tesy_schedule_sidebar_visibility").async_load()
        state["visible"] = bool(saved.get("visible", True)) if isinstance(saved, dict) else True
    return state

def _register_panel(hass, state):
    if frontend.async_panel_exists(hass, PANEL_PATH):
        if not state.get("panel_owned"):
            return
        frontend.async_remove_panel(hass, PANEL_PATH)
    frontend.async_register_built_in_panel(
        hass, component_name="custom", frontend_url_path=PANEL_PATH,
        sidebar_title="TESY schedules", sidebar_icon="mdi:calendar-edit",
        config={"_panel_custom": {"name": PANEL_NAME,
            "module_url": EDITOR_ASSET, "embed_iframe": False,
            "trust_external": False, "handle_safe_area": False}},
        require_admin=True, show_in_sidebar=state["visible"])
    state["panel_owned"] = True

async def async_setup_editor(hass):
    state = await async_sidebar_state(hass)
    if "frontend" not in hass.config.components or getattr(hass, "http", None) is None:
        return
    if state.get("ready"):
        return
    base = Path(__file__).parent / "www"
    if not state.get("static_paths_registered"):
        await hass.http.async_register_static_paths([
            StaticPathConfig(EDITOR_ASSET, str(base / "schedule-editor.js"), False),
            StaticPathConfig(ENTITY_ASSET, str(base / "schedule-entity.js"), False),
        ])
        state["static_paths_registered"] = True
    frontend.add_extra_js_url(hass, ENTITY_ASSET)
    _register_panel(hass, state)
    state["ready"] = True

async def async_set_sidebar_visible(hass, visible):
    """Change Home Assistant sidebar presence only, never the heater program."""
    state = await async_sidebar_state(hass)
    visible = bool(visible)
    if state["visible"] == visible:
        return
    state["visible"] = visible
    if state.get("ready") and state.get("panel_owned"):
        _register_panel(hass, state)
    await Store(hass, 1, "mytesy_schedule_sidebar_visibility").async_save({"visible": visible})
    for entity in list(state.get("switch_entities", [])):
        if entity.hass is not None:
            entity.async_write_ha_state()

async def async_unload_editor(hass):
    state = hass.data.get(DOMAIN, {}).get("_editor", {})
    if not state.get("ready"):
        return
    if state.get("panel_owned"):
        frontend.async_remove_panel(hass, PANEL_PATH)
    frontend.remove_extra_js_url(hass, ENTITY_ASSET)
    state["ready"] = False
